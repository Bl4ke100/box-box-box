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
    feats_add = np.zeros(225)
    feats_mult = np.zeros(225)
    
    total_laps = race_config['total_laps']
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    plt = race_config['pit_lane_time']
    blt = race_config['base_lap_time']
    
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
                feats_add[c_idx * 75 + 74] += 1
                feats_mult[c_idx * 75 + 74] += blt
            else:
                feats_add[c_idx * 75 + age - 1] += 1
                feats_mult[c_idx * 75 + age - 1] += blt
                
    return np.hstack([feats_add, feats_mult]), plt * len(stops)

A_diff = []
C_diff = []

best_temp = 32

for race in races:
    config = race['race_config']
    if config['track_temp'] != best_temp:
        continue
        
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1, c1 = get_feats_arr(config, strats[d1])
        f2, c2 = get_feats_arr(config, strats[d2])
        
        diff_f = f1 - f2
        diff_C = c1 - c2
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_C)

A = np.array(A_diff)
C = np.array(C_diff)

print(f"Total inequalities for Temp {best_temp} (Dual Add/Mult): {len(A)}")

# 450 variables
c = np.zeros(450)
b_ub = -C - 0.001

A_mono = []
for c_id in range(3):
    for age in range(74):
        # W_{add, age} - W_{add, age+1} <= 0
        row1 = np.zeros(450)
        row1[c_id * 75 + age] = 1
        row1[c_id * 75 + age + 1] = -1
        A_mono.append(row1)
        
        row2 = np.zeros(450)
        row2[225 + c_id * 75 + age] = 1
        row2[225 + c_id * 75 + age + 1] = -1
        A_mono.append(row2)

A_mono = np.array(A_mono)
b_mono = np.zeros(len(A_mono))

A_full = np.vstack([A, A_mono])
b_full = np.hstack([b_ub, b_mono])

bounds = [(None, None)] * 450

res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')
print("Status Dual:", res.status, res.message)

