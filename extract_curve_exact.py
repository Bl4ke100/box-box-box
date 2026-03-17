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

# Let's map (compound, age) to a discrete variable.
# Assume max age is 60. Max temp is ignored for a second.
# Wait, if temp interacts, maybe we just isolate ONE temp value to plot the curve!
# Let's find all pairs that have the exact same track_temp = 27 (or whatever is common).

temp_counts = {}
for race in races[:200]:
    t = race['race_config']['track_temp']
    temp_counts[t] = temp_counts.get(t, 0) + 1

best_temp = max(temp_counts, key=temp_counts.get)
print(f"Isolating Temp = {best_temp} (Found in {temp_counts[best_temp]} races)")

# Let's just solve for W_{c, age} for Temp = best_temp
# 3 compounds * 75 max age = 225 variables
c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_feats_arr(race_config, strat):
    # Vector of size 225 + 1 (pit stops)
    features = np.zeros(225 + 1)
    
    total_laps = race_config['total_laps']
    plt = race_config['pit_lane_time']
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    features[225] = plt * len(stops) # the constant pit time
    
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
                # clip to 75 just in case
                features[c_idx * 75 + 74] += 1
            else:
                features[c_idx * 75 + age - 1] += 1
                
    return features

A_diff = []
C_diff = []

for race in races:  # We need to search all races to find enough equations for this temp
    config = race['race_config']
    if config['track_temp'] != best_temp:
        continue
        
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
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

print(f"Total inequalities for Temp {best_temp}: {len(A)}")

c = np.zeros(225)
b_ub = -C - 0.001

# Add monotonic bounds: W_{age+1} >= W_{age} for each compound
A_mono = []
for c_id in range(3):
    for age in range(74):
        # W_{age} - W_{age+1} <= 0
        row = np.zeros(225)
        row[c_id * 75 + age] = 1
        row[c_id * 75 + age + 1] = -1
        A_mono.append(row)

A_mono = np.array(A_mono)
b_mono = np.zeros(len(A_mono))

A_full = np.vstack([A, A_mono])
b_full = np.hstack([b_ub, b_mono])

bounds = [(0.0, None)] * 225

print("Solving LP for explicit non-parametric curve...")
res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')

if res.success:
    print("MAPPED PERFECT CURVE!")
    W = res.x
    for c_name, c_id in c_idx_map.items():
        print(f"\n{c_name} Curve (Age 1 to 30):")
        vals = W[c_id * 75 : c_id * 75 + 30]
        print(np.round(vals, 4))
else:
    print("Optimization failed.")
    print("Status:", res.status)
