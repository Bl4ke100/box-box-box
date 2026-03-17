import numpy as np
from scipy.optimize import linprog
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_feats_arr(race_config, strat):
    # Vector of size 225
    features = np.zeros(225)
    
    total_laps = race_config['total_laps']
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    
    for stop in stops:
        pit_lap = stop['lap']
        stints.append((current_tire, pit_lap - current_lap + 1))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
        
    for tire, slen in stints:
        c_idx = c_idx_map[tire]
        for age in range(1, slen + 1):
            if age > 75:
                features[c_idx * 75 + 74] += 1
            else:
                features[c_idx * 75 + age - 1] += 1
                
    # Multiply by base_lap_time! Because lap_time = base_lap_time * (1 + W_c_age)
    # Wait! If lap_time = base_lap_time * (1 + W), then the sum over the race is:
    # 50 * base_lap_time + base_lap_time * sum(W)
    # So the feature multiplier is base_lap_time!
    blt = race_config['base_lap_time']
    return features * blt

A_diff = []
C_diff = []

best_temp = 32

for race in races:
    config = race['race_config']
    if config['track_temp'] != best_temp:
        continue
        
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    plt = config['pit_lane_time']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1 = get_feats_arr(config, strats[d1])
        f2 = get_feats_arr(config, strats[d2])
        
        c1 = plt * len(strats[d1]['pit_stops'])
        c2 = plt * len(strats[d2]['pit_stops'])
        
        diff_f = f1 - f2
        diff_C = c1 - c2
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_C)

A = np.array(A_diff)
C = np.array(C_diff)

print(f"Total inequalities for Temp {best_temp} (Multiplicative): {len(A)}")

c = np.zeros(225)
b_ub = -C - 0.001

A_mono = []
for c_id in range(3):
    for age in range(74):
        row = np.zeros(225)
        row[c_id * 75 + age] = 1
        row[c_id * 75 + age + 1] = -1
        A_mono.append(row)

A_mono = np.array(A_mono)
b_mono = np.zeros(len(A_mono))

A_full = np.vstack([A, A_mono])
b_full = np.hstack([b_ub, b_mono])

bounds = [(None, None)] * 225

res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')
print("Status:", res.status, res.message)

