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

def get_hybrid_feats(race_config, strat):
    # Vector of size 3 (Compound Multipliers) + 225 (W_c_age) + 1 (Constant Pit)
    features = np.zeros(3 + 225 + 1)
    
    total_laps = race_config['total_laps']
    plt = race_config['pit_lane_time']
    blt = race_config['base_lap_time']
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    features[-1] = plt * len(stops)
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
        # Multiply by base_lap_time
        features[c_idx] += slen * blt
        
        for age in range(1, slen + 1):
            if age > 75:
                # clip to 75
                features[3 + c_idx * 75 + 74] += 1
            else:
                features[3 + c_idx * 75 + age - 1] += 1
                
    return features

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]

A_diff = []
C_diff = []

for idx, race in enumerate(valid_races):
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    race_A = []
    race_C = []
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1 = get_hybrid_feats(config, strats[d1])
        f2 = get_hybrid_feats(config, strats[d2])
        
        diff_f = f1[:228] - f2[:228]
        diff_C = f1[228] - f2[228]
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            race_A.append(diff_f)
            race_C.append(diff_C)
            
    A_diff.extend(race_A)
    C_diff.extend(race_C)
    
    A = np.array(A_diff)
    C = np.array(C_diff)
    
    c = np.zeros(228)
    b_ub = -C
    
    A_mono = []
    for c_id in range(3):
        for age in range(74):
            # W[age] <= W[age+1] -> W[age] - W[age+1] <= 0
            row = np.zeros(228)
            row[3 + c_id * 75 + age] = 1
            row[3 + c_id * 75 + age + 1] = -1
            A_mono.append(row)
            
    # Compound multiplier ordering: SOFT < MEDIUM < HARD
    # C_S - C_M <= 0 -> Soft is numerically faster (wait. multiplier should be smaller for faster!)
    # Soft lap time = Base * C_S. If C_S = 0.98, Medium = 1.0, Hard = 1.02.
    # So C_S < C_M < C_H
    row_s_m = np.zeros(228)
    row_s_m[0] = 1
    row_s_m[1] = -1
    A_mono.append(row_s_m)
    
    row_m_h = np.zeros(228)
    row_m_h[1] = 1
    row_m_h[2] = -1
    A_mono.append(row_m_h)
            
    A_mono = np.array(A_mono)
    b_mono = np.zeros(len(A_mono))
    
    A_full = np.vstack([A, A_mono])
    b_full = np.hstack([b_ub, b_mono])
    
    # Base multiplier > 0.0. Degradation >= 0.0
    bounds = [(0.0, None)] * 228
    
    res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')
    
    if not res.success:
        print(f"Broke at Race {idx + 1} with HYBRID model and margin 0.0!")
        break
    else:
        print(f"Passed Race {idx + 1}")

if res.success:
    print("ALL RACES PASSED WITH HYBRID MODEL!")
    print(np.round(res.x[:3], 4))

