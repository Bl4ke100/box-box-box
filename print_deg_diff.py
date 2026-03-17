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
        row = np.zeros(228)
        row[3 + c_id * 75 + age] = 1
        row[3 + c_id * 75 + age + 1] = -1
        A_mono.append(row)
        
    for age in range(73):
        row = np.zeros(228)
        row[3 + c_id * 75 + age] = -1
        row[3 + c_id * 75 + age + 1] = 2
        row[3 + c_id * 75 + age + 2] = -1
        A_mono.append(row)

row_M_ground = np.zeros(228)
row_M_ground[1] = 1
A_eq = np.array([row_M_ground])
b_eq = np.array([0.0])

A_mono = np.array(A_mono)
b_mono = np.zeros(len(A_mono))

A_full = np.vstack([A, A_mono])
b_full = np.hstack([b_ub, b_mono])

bounds = [(-5.0, 5.0)] * 3 + [(0.0, None)] * 225

res = linprog(c, A_ub=A_full, b_ub=b_full, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

if res.success:
    W = res.x
    s_deg = W[3:78]
    s_diff = np.diff(np.insert(s_deg, 0, 0))
    m_deg = W[78:153]
    m_diff = np.diff(np.insert(m_deg, 0, 0))
    h_deg = W[153:228]
    h_diff = np.diff(np.insert(h_deg, 0, 0))

    with open("curve_output.txt", "w") as f:
        f.write(f"COMPOUNDS (S, M, H): {W[:3]}\n\n")
        f.write("SOFT DEG PER LAP:\n" + np.array2string(s_diff[:40], max_line_width=200, threshold=np.inf) + "\n\n")
        f.write("MEDIUM DEG PER LAP:\n" + np.array2string(m_diff[:40], max_line_width=200, threshold=np.inf) + "\n\n")
        f.write("HARD DEG PER LAP:\n" + np.array2string(h_diff[:40], max_line_width=200, threshold=np.inf) + "\n")
