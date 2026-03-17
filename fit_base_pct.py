import numpy as np
from scipy.optimize import minimize
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
    # Features:
    # 0,1,2: S, M, H laps * base_lap_time
    # 3,4,5: S, M, H age sum
    # 6,7,8: S, M, H age * temp sum
    
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
        
        # Compound offset multiplied by base_lap_time!
        features[idx] += stint_len * base_lap_time
        
        ages = np.arange(1, stint_len + 1)
        features[3 + idx] += np.sum(ages)
        features[6 + idx] += np.sum(ages * temp)
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len * base_lap_time
        ages = np.arange(1, stint_len + 1)
        features[3 + idx] += np.sum(ages)
        features[6 + idx] += np.sum(ages * temp)
        
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
        diff_c = c1 - c2
        if any(abs(v) > 0.001 for v in diff_f):
            A_diff.append(diff_f)
            C_diff.append(diff_c)

A = np.array(A_diff)
C = np.array(C_diff)

def loss(W):
    v = np.dot(A, W) + C
    return np.sum(np.maximum(0, v + 0.001)**2)

bounds = [(0,0)] + [(None, None)] * 8

res = minimize(loss, np.zeros(9), method='L-BFGS-B', bounds=bounds)

print(f"Percentage Base Interaction Loss: {res.fun:.4f}")
print("Violations:", np.sum(np.dot(A, res.x) + C > -0.001))
np.set_printoptions(suppress=True, precision=6)
print("W:", res.x)
