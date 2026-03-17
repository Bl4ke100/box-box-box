import numpy as np
from scipy.optimize import differential_evolution
import json
import glob
import os

def main():
    data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
    files = glob.glob(os.path.join(data_dir, "*.json"))

    races = []
    for f in files[:8]:
        with open(f, 'r') as fin:
            races.extend(json.load(fin))

    def get_feats(race_config, strat):
        # Just the 9 basic features + pit lane
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
            features[3+idx] += stint_len * (stint_len + 1) / 2
            features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
            
            current_lap = pit_lap + 1
            current_tire = stop['to_tire']
            
        if current_lap <= total_laps:
            stint_len = total_laps - current_lap + 1
            idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
            features[idx] += stint_len
            features[3+idx] += stint_len * (stint_len + 1) / 2
            features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
            
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
            
            if not (all(abs(v) < 0.001 for v in diff_f) and abs(diff_C) < 0.001):
                A_diff.append(diff_f)
                C_diff.append(diff_C)

    A = np.array(A_diff)
    C = np.array(C_diff)

    print(f"Total non-tied inequalities: {len(A)}")

    def loss(W):
        # W is length 9
        arr_W = np.zeros(9)
        arr_W[1:] = W # base Soft is 0 automatically
        
        # We want to minimize the number of violations.
        v = np.dot(A, arr_W) + C
        violations = np.sum(v > -0.000001)
        
        v_positive = np.maximum(0, v)
        return violations + np.mean(v_positive) * 0.01

    bounds = [
        (0.5, 3.0), (1.0, 3.5), # base M, H
        (0.1, 0.5), (0.05, 0.3), (0.01, 0.15), # deg S, M, H
        (0.0001, 0.005), (0.0001, 0.005), (0.0001, 0.005) # temp S, M, H
    ]

    print("Starting DE solver...")
    res = differential_evolution(loss, bounds, maxiter=200, workers=1, popsize=20, disp=True)

    print("Best loss:", res.fun)
    arr_W = np.zeros(9)
    arr_W[1:] = res.x
    print("Best W:", arr_W)
    v = np.dot(A, arr_W) + C
    print("Absolute violations:", np.sum(v > -0.000001))

if __name__ == '__main__':
    main()
