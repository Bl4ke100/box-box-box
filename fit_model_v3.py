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

def get_feats(race_config, strat, exponent=2):
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    features = [0.0] * 9
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    def add_stint(c_tire, stint_len):
        idx = 0 if c_tire == 'SOFT' else (1 if c_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        # sum of age^exponent
        ages = np.arange(1, stint_len + 1)
        sum_age = np.sum(ages ** exponent)
        features[3 + idx] += sum_age
        features[6 + idx] += sum_age * temp

    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        add_stint(current_tire, stint_len)
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        add_stint(current_tire, stint_len)
        
    return features, constant_time

for exp in [1.5, 2.0]:  # Try different degradation shapes
    A_diff = []
    C_diff = []

    for race in races[:1000]:
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        
        for i in range(len(finishing) - 1):
            d1 = finishing[i]
            d2 = finishing[i+1]
            
            f1, c1 = get_feats(config, strats[d1], exponent=exp)
            f2, c2 = get_feats(config, strats[d2], exponent=exp)
            
            diff_f = [x1 - x2 for x1, x2 in zip(f1, f2)]
            diff_c = c1 - c2
            
            if any(abs(v) > 0.001 for v in diff_f):
                A_diff.append(diff_f)
                C_diff.append(diff_c)

    A = np.array(A_diff)
    C = np.array(C_diff)

    def loss(W):
        v = np.dot(A, W) + C
        return np.sum(np.maximum(0, v + 0.01)**2)

    res = minimize(loss, np.zeros(9), method='L-BFGS-B', bounds=[(0.0, None)]*9)
    print(f"\nExponent {exp}: Loss={res.fun:.4f}, Violations={np.sum(np.dot(A, res.x) + C > -0.001)}")
    if res.fun < 1000:
        W = res.x
        print(f"Base S, M, H: {W[0]:.6f}, {W[1]:.6f}, {W[2]:.6f}")
        print(f"Deg S, M, H: {W[3]:.6f}, {W[4]:.6f}, {W[5]:.6f}")
        print(f"Temp S, M, H: {W[6]:.6f}, {W[7]:.6f}, {W[8]:.6f}")
