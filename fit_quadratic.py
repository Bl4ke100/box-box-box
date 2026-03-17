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
    # Let's add quadratic features!
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    # 0,1,2: S/M/H laps
    # 3,4,5: S/M/H linear age
    # 6,7,8: S/M/H linear temp
    # 9,10,11: S/M/H quadratic age
    # 12,13,14: S/M/H quadratic temp
    features = [0.0] * 15
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        stints.append((current_tire, stint_len))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        stints.append((current_tire, stint_len))
        
    for tire, slen in stints:
        idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
        features[idx] += slen
        
        sum_age = slen * (slen + 1) / 2
        features[3+idx] += sum_age
        features[6+idx] += sum_age * temp
        
        sum_sq = slen * (slen + 1) * (2*slen + 1) / 6
        features[9+idx] += sum_sq
        features[12+idx] += sum_sq * temp
        
    return features, constant_time

A_diff = []
C_diff = []

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
        diff_C = c1 - c2
        
        A_diff.append(diff_f)
        C_diff.append(diff_C)

A = np.array(A_diff)
C = np.array(C_diff)

print(f"Total inequalities: {len(A)}")

# Minimize 0 to just find feasibility
c = np.zeros(15)
b_ub = -C - 0.001 # Margin of 0.001

bounds = [(None, None)] * 15
bounds[0] = (0.0, 0.0) # anchor S base to 0

print("Solving linprog with Quadratic bounds...")
res = linprog(c, A_ub=A, b_ub=b_ub, bounds=bounds, method='highs')

if res.success:
    W = res.x
    print(f"BINGO! Exact Mathematical Solution Found!")
    print(np.round(W, 6))
else:
    print("Optimization failed.")
    print("Status:", res.status)
    print("Message:", res.message)

