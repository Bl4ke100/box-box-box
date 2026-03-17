import numpy as np
import json
import glob
import os
import itertools

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

# Build pairs for 1000 races
print("Building pairs...")
A_diff = []
C_diff = []

for race in races[:1000]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    # Only need to check adjacent pairs! If sorted perfectly, transitivity holds.
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1, c1 = get_feats(config, strats[d1])
        f2, c2 = get_feats(config, strats[d2])
        
        diff_f = [x1 - x2 for x1, x2 in zip(f1, f2)]
        diff_c = c1 - c2
        
        A_diff.append(diff_f)
        C_diff.append(diff_c)

A = np.array(A_diff)
C = np.array(C_diff)
print(f"Total pairs: {A.shape[0]}")

base_M = [1.25, 1.3, 1.35]
base_H = [2.1, 2.2, 2.25]
deg_S = [0.28, 0.29, 0.30, 0.31]
deg_M = [0.10, 0.11, 0.12]
deg_H = [0.04, 0.05, 0.06]
temp_S = [0.0014, 0.0015, 0.0016]
temp_M = [0.0007, 0.00075, 0.0008]
temp_H = [0.0003, 0.0004, 0.0005]

best_v = float('inf')
best_W = None

print("Starting grid search...")
for bM in base_M:
    for bH in base_H:
         for dS in deg_S:
              for dM in deg_M:
                   for dH in deg_H:
                        for tS in temp_S:
                             for tM in temp_M:
                                  for tH in temp_H:
                                       W = np.array([0.0, bM, bH, dS, dM, dH, tS, tM, tH])
                                       v = np.dot(A, W) + C
                                       # We only count strictly positive violations
                                       violations = np.sum(v > 0.0001)
                                       if violations < best_v:
                                           best_v = violations
                                           best_W = tuple(W)
                                           print(f"New best: {best_v} violations -> {best_W}")
                                           if best_v == 0:
                                               print("FOUND PERFECT EXACT PARAMS!")
                                               exit(0)

print(f"Final best: {best_v} violations -> {best_W}")
