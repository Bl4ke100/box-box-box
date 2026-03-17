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
    features = np.zeros(225 + 1)
    total_laps = race_config['total_laps']
    plt = race_config['pit_lane_time']
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    features[225] = plt * len(stops)
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
            features[c_idx * 75 + age - 1] += 1
                
    return features

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]

def extract_curve_for_race(race):
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    A_diff = []
    C_diff = []
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1 = get_feats_arr(config, strats[d1])
        f2 = get_feats_arr(config, strats[d2])
        
        diff_f = f1[:225] - f2[:225]
        diff_C = f1[225] - f2[225]
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_C)

    A = np.array(A_diff)
    C = np.array(C_diff)
    
    c = np.zeros(225)
    c += 0.0001
    c[0:75] += 0.0001
    c[75:150] += 0.0002
    c[150:225] += 0.0003

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
    bounds = [(0.0, None)] * 225

    res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')
    
    if res.success:
        return res.x
    return None

W1 = extract_curve_for_race(valid_races[0])
W2 = extract_curve_for_race(valid_races[1])

if W1 is not None and W2 is not None:
    print(f"RACE 0 CONFIG: {valid_races[0]['race_config']}")
    print(f"RACE 1 CONFIG: {valid_races[1]['race_config']}")
    
    for c_name, c_id in c_idx_map.items():
        print(f"\n{c_name} Curve Race 0 (Age 1 to 20):")
        print([round(v, 4) for v in W1[c_id * 75 : c_id * 75 + 20]])
        
        print(f"\n{c_name} Curve Race 1 (Age 1 to 20):")
        print([round(v, 4) for v in W2[c_id * 75 : c_id * 75 + 20]])
else:
    print("Could not extract optimal curves for one of the races.")

