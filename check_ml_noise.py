import json
import glob
import os
import numpy as np

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
    # Just the 9 basic features + pit lane + diff C
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    features = [0.0] * 9
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
        
    return features, constant_time

X_dict = {}
contradictions = 0
total_pairs = 0

# Test ALL pairs in a race
for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    feats = {d_id: get_feats(config, strats[d_id]) for d_id in finishing}
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            
            f1, c1 = feats[d1]
            f2, c2 = feats[d2]
            
            diff = tuple(np.round([x1 - x2 for x1, x2 in zip(f1, f2)], 3))
            diff_C = round(c1 - c2, 3)
            
            # Label
            y = 1
            
            key = (diff, diff_C, config['track_temp'], config['pit_lane_time'], config['base_lap_time'], config['total_laps'])
            
            total_pairs += 1
            if key in X_dict:
                if X_dict[key] != y:
                    contradictions += 1
            else:
                X_dict[key] = y
                
            y_inv = 0
            diff_inv = tuple(np.round([-x for x in diff], 3))
            diff_C_inv = round(-diff_C, 3)
            key_inv = (diff_inv, diff_C_inv, config['track_temp'], config['pit_lane_time'], config['base_lap_time'], config['total_laps'])
            
            total_pairs += 1
            if key_inv in X_dict:
                if X_dict[key_inv] != y_inv:
                    contradictions += 1
            else:
                X_dict[key_inv] = y_inv

print(f"Total Samples (2 directions per pair): {total_pairs}")
print(f"Total Identical Vectors with Different Labels: {contradictions}")

