import numpy as np
from scipy.optimize import linprog
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:10]: # ~20000 pairs
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

A_diff = []
C_diff = []

for race in races:
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
        
        if any(abs(v) > 0.001 for v in diff_f):
            A_diff.append(diff_f)
            C_diff.append(diff_c)

A = np.array(A_diff)
C = np.array(C_diff)

print(f"Total inequalities: {len(A)}")

# We want diff_f * W <= -diff_c - M
# So diff_f * W + M <= -diff_c

# To prevent Unbounded, we do NOT maximize M as an unbounded objective.
# Instead, we just want ANY feasible W that satisfies diff_f * W <= -diff_c - 0.001
# So we set M = 0.001 as a fixed constant in the vector!
# Then objective is just minimize 0 (find feasible point).
# To find a "centered" clean parameter set, we can minimize sum of variables (L1 regularize)
c = np.ones(9)

bounds = [(0, 10)] * 9 # Keep components within reasonable bounds to prevent shooting to infinity

# Anchor S_base to 0, since we just need relative offsets.
bounds[0] = (0, 0)
# We know other bases are ~1 to 3
bounds[1] = (0.5, 3.0)
bounds[2] = (1.0, 5.0)

b_ub = -C - 0.001

print("Solving linprog...")
res = linprog(c, A_ub=A, b_ub=b_ub, bounds=bounds, method='highs')

if res.success:
    W = res.x
    print(f"Success!")
    print(f"Base S, M, H: {W[0]:.6f}, {W[1]:.6f}, {W[2]:.6f}")
    print(f"Deg S, M, H: {W[3]:.6f}, {W[4]:.6f}, {W[5]:.6f}")
    print(f"Temp S, M, H: {W[6]:.6f}, {W[7]:.6f}, {W[8]:.6f}")
else:
    print("Optimization failed.")
    print("Status:", res.status) # 2 = infeasible, 3 = unbounded
    print("Message:", res.message)

