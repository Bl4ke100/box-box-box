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

def get_rev_hybrid_feats(race_config, strat):
    features = np.zeros(3 + 225)
    total_laps = race_config['total_laps']
    plt = race_config['pit_lane_time']
    blt = race_config['base_lap_time']
    
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
        features[c_idx] += slen
        
        for age in range(1, slen + 1):
            if age > 75:
                features[3 + c_idx * 75 + 74] += 1 * blt
            else:
                features[3 + c_idx * 75 + age - 1] += 1 * blt
                
    return features, plt * len(stops)

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]

eval_races = valid_races[:60]

A_diff = []
C_diff = []

for idx, race in enumerate(eval_races):
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1, c1 = get_rev_hybrid_feats(config, strats[d1])
        f2, c2 = get_rev_hybrid_feats(config, strats[d2])
        
        diff_f = f1 - f2
        diff_C = c1 - c2
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_C)
            
A = np.array(A_diff)
C = np.array(C_diff)

c = np.zeros(228)
c[3:228] = 0.01

b_ub = -C

A_mono = []
for c_id in range(3):
    for age in range(74):
        # W[age] <= W[age+1] -> W[age] - W[age+1] <= 0
        row = np.zeros(228)
        row[3 + c_id * 75 + age] = 1
        row[3 + c_id * 75 + age + 1] = -1
        A_mono.append(row)
        
    for age in range(73):
        # Convexity: W[age+2] - 2*W[age+1] + W[age] >= 0
        # -> -W[age+2] + 2*W[age+1] - W[age] <= 0
        row = np.zeros(228)
        row[3 + c_id * 75 + age] = -1
        row[3 + c_id * 75 + age + 1] = 2
        row[3 + c_id * 75 + age + 2] = -1
        A_mono.append(row)

A_mono = np.array(A_mono)
b_mono = np.zeros(len(A_mono))

A_full = np.vstack([A, A_mono])
b_full = np.hstack([b_ub, b_mono])

bounds = [(-5.0, 5.0)] * 3 + [(0.0, None)] * 225

res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')

if res.success:
    W = res.x
    np.set_printoptions(suppress=True, precision=6)
    print("COMPOUNDS (S, M, H):", W[:3])
    print("SOFT DEG:", W[3:23])
    print("MEDIUM DEG:", W[78:98])
    print("HARD DEG:", W[153:173])
else:
    print("Infeasible")

