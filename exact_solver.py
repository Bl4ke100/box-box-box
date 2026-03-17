import json
import os
import glob

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
    # Features: [S_laps, M_laps, H_laps, S_age, M_age, H_age, S_temp, M_temp, H_temp]
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    features = [0.0] * 9
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        features[idx] += stint_len
        sum_age = stint_len * (stint_len + 1) / 2
        features[3 + idx] += sum_age
        features[6 + idx] += sum_age * temp
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        sum_age = stint_len * (stint_len + 1) / 2
        features[3 + idx] += sum_age
        features[6 + idx] += sum_age * temp
        
    return features, constant_time

with open('differences.txt', 'w') as out:
    for race in races:
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        
        for i in range(len(finishing) - 1):
            d1 = finishing[i]
            d2 = finishing[i+1]
            
            f1, c1 = get_feats(config, strats[d1])
            f2, c2 = get_feats(config, strats[d2])
            
            diff = [round(x - y, 2) for x, y in zip(f1, f2)]
            
            non_zero = sum(1 for x in diff if abs(x) > 0.01)
            # Find super close drivers where difference is very sparse!
            if non_zero <= 4 and abs(c1 - c2) < 0.01:
                out.write(f"Track {config['track']}, Temp {config['track_temp']}, Diff: {diff}\n")
