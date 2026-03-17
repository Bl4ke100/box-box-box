import numpy as np
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
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

# W_rounded = [0.0, 1.3, 2.2, 0.3, 0.1, 0.05, 0.0015, 0.00075, 0.0004]

W_rounded = [0.0, 1.3, 2.2, 0.3, 0.1, 0.05, 0.0015, 0.00075, 0.0004]

violations = []

for race in races[:1000]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1, c1 = get_feats(config, strats[d1])
        f2, c2 = get_feats(config, strats[d2])
        
        diff_f = [x1 - x2 for x1, x2 in zip(f1, f2)]
        diff_c = c1 - c2
        
        # Exclude exact feature ties
        if not (all(abs(v) < 0.001 for v in diff_f) and abs(diff_c) < 0.001):
            v = np.dot(diff_f, W_rounded) + diff_c
            if v > 0.001:  # d1 was predicted strictly slower than d2, but finished AHEAD!
                violations.append((v, d1, d2, diff_f, diff_c, config))

# Print the top 5 largest violations
violations.sort(key=lambda x: x[0], reverse=True)
print(f"Total isolated strict structural violations: {len(violations)}")
for count, (v, d1, d2, df, dc, config) in enumerate(violations[:5]):
    print(f"\nViolation {count+1}: Predicted D1 ({d1}) slower by {v:.4f} seconds")
    print(f"Track Temp: {config['track_temp']}, Pit Penalty: {config['pit_lane_time']}")
    print(f"Diff Features (F1-F2): {df}")
    print(f"Diff Constant (C1-C2): {dc}")

