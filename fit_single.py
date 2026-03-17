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

race = races[0]
config = race['race_config']
strats = {s['driver_id']: s for _, s in race['strategies'].items()}
finishing = race['finishing_positions']

A_diff = []
C_diff = []

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

c = np.zeros(10)
c[9] = -1.0 # margin

A_ext = np.zeros((A.shape[0], 10))
A_ext[:, :9] = A
A_ext[:, 9] = 1.0 # + M

bounds = [(None, None)] * 9 + [(0, None)]

res = linprog(c, A_ub=A_ext, b_ub=-C, bounds=bounds)

if res.success:
    W = res.x[:9]
    M = res.x[9]
    print(f"Success! Margin: {M}")
    print(f"Base S, M, H: {W[0]:.6f}, {W[1]:.6f}, {W[2]:.6f}")
    print(f"Deg S, M, H: {W[3]:.6f}, {W[4]:.6f}, {W[5]:.6f}")
    print(f"Temp S, M, H: {W[6]:.6f}, {W[7]:.6f}, {W[8]:.6f}")
else:
    print("Optimization failed.")
