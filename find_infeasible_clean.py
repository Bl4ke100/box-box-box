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

A_diff = []
C_diff = []
pairs = []

for race in races[:200]:
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
        if not (all(abs(v) < 0.001 for v in diff_f) and abs(diff_c) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_c)
            pairs.append((d1, d2, config, strats[d1], strats[d2], f1, f2, c1, c2))

A = np.array(A_diff)
C = np.array(C_diff)

c = np.zeros(9)
bounds = [(None, None)] * 9
bounds[0] = (0.0, 0.0)

for i in range(1, len(pairs) + 1):
    b_ub = -C[:i] - 0.01

    res = linprog(c, A_ub=A[:i], b_ub=b_ub, bounds=bounds, method='highs')

    if not res.success:
        print(f"Infeasible at pair index {i-1}: {pairs[i-1][0]} vs {pairs[i-1][1]}")
        print("Previous successful subset was 0 to", i-2)
        
        p = pairs[i-1]
        print(f"\nConflicting Pair config: temp={p[2]['track_temp']}, pit={p[2]['pit_lane_time']}")
        print(f"D1 {p[0]}: {p[3]['starting_tire']} -> {p[3]['pit_stops']}")
        print(f"D2 {p[1]}: {p[4]['starting_tire']} -> {p[4]['pit_stops']}")
        print(f"diff_f: {A[i-1]}")
        print(f"diff_c: {C[i-1]}")
        
        # Let's also print the specific indices that cause the conflict.
        # It's bounded by previous successful subset, so this pair conflicts with SOME previous subset.
        break

