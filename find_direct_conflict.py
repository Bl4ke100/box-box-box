import numpy as np
from scipy.optimize import linprog

c10_f = np.array([-1.0, -33.0, 34.0, -17.0, -561.0, 307.0, -459.0, -15147.0, 8289.0])
c10_c = 22.7

c11_f = np.array([2.0, -2.0, 0.0, 33.0, -69.0, 0.0, 891.0, -1863.0, 0.0])
c11_c = 0.0

# Actually I need the real pairs array from find_infeasible_clean!
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
            pairs.append((d1, d2, config, diff_f, diff_c))

A = np.array(A_diff)
C = np.array(C_diff)

c = np.zeros(9)
bounds = [(None, None)] * 9
bounds[0] = (0.0, 0.0)

# We know 0..11 is infeasible.
A_sub = A[:12]
C_sub = C[:12]

# Let's remove exactly 1 constraint from 0 to 10 and see if it becomes feasible
for remove_idx in range(11):
    A_test = np.delete(A_sub, remove_idx, axis=0)
    C_test = np.delete(C_sub, remove_idx)
    
    b_ub = -C_test - 0.01
    res = linprog(c, A_ub=A_test, b_ub=b_ub, bounds=bounds, method='highs')
    
    if res.success:
        print(f"BINGO! Constraint {remove_idx} directly contradicts Constraint 11 (in combination with the others)!")
        
        # Let's see if Constraint {remove_idx} and Constraint 11 ALONE are contradictory
        A_pair = np.vstack([A_sub[remove_idx], A_sub[11]])
        b_pair = np.array([-C_sub[remove_idx] - 0.01, -C_sub[11] - 0.01])
        res_pair = linprog(c, A_ub=A_pair, b_ub=b_pair, bounds=bounds, method='highs')
        if not res_pair.success:
            print("AND THEY ARE DIRECTLY CONTRADICTORY AS A PAIR!")
            break
        else:
            print("But they require the other 10 constraints to be contradictory.")
