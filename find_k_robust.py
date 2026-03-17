import numpy as np
from scipy.optimize import minimize
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_base_feats(race_config, strat):
    total_laps = race_config['total_laps']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    stints = []
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        stints.append((current_tire, stint_len))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        stints.append((current_tire, stint_len))
        
    return stints, constant_time, race_config['track_temp']

race_data = [] 
for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    drivers_info = []
    for d_id in finishing:
        stints, c, temp = get_base_feats(config, strats[d_id])
        drivers_info.append((stints, c))
    race_data.append((config['track_temp'], drivers_info))

def compute_race_features(temp, drivers_info, kS, kM, kH):
    k_map = {'SOFT': kS, 'MEDIUM': kM, 'HARD': kH}
    idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}
    
    diffs_f = []
    diffs_c = []
    
    driver_feats = []
    for stints, c in drivers_info:
        f = [0.0] * 9
        for tire, length in stints:
            idx = idx_map[tire]
            f[idx] += length
            
            k = k_map[tire]
            if length > k:
                # lap ages from k+1 to length meaning effective age starts from 1
                n = length - k
                sum_eff_age = n * (n + 1) / 2
                f[3 + idx] += sum_eff_age
                f[6 + idx] += sum_eff_age * temp
        driver_feats.append(f)
        
    for i in range(len(drivers_info) - 1):
        f1 = driver_feats[i]
        c1 = drivers_info[i][1]
        f2 = driver_feats[i+1]
        c2 = drivers_info[i+1][1]
        
        diff = [x1 - x2 for x1, x2 in zip(f1, f2)]
        diff_c = c1 - c2
        diffs_f.append(diff)
        diffs_c.append(diff_c)
        
    return diffs_f, diffs_c

def eval_loss(kS, kM, kH):
    A_diff = []
    C_diff = []
    
    for temp, drivers_info in race_data:
        df, dc = compute_race_features(temp, drivers_info, kS, kM, kH)
        for d_f, d_c in zip(df, dc):
            if any(abs(v) > 0.001 for v in d_f):
                A_diff.append(d_f)
                C_diff.append(d_c)
                
    A = np.array(A_diff)
    C = np.array(C_diff)
    
    def loss(W):
        v = np.dot(A, W) + C
        return np.sum(np.maximum(0, v + 0.001)**2)
        
    res = minimize(loss, np.zeros(9), method='L-BFGS-B', bounds=[(0.0, None)] * 9)
    return res.fun, res.x

if __name__ == '__main__':
    best_loss = float('inf')
    best_k = None
    best_w = None

    for kS in [0, 2, 5, 8]:
        for kM in [0, 5, 10, 15]:
            for kH in [0, 10, 15, 20]:
                loss_val, w = eval_loss(kS, kM, kH)
                if loss_val < best_loss:
                    best_loss = loss_val
                    best_k = (kS, kM, kH)
                    best_w = w
                    print(f"New best: k={best_k}, loss={best_loss:.4f}")

    print(f"Final best K: {best_k}")
    np.set_printoptions(suppress=True, precision=5)
    print(f"Final best W: {best_w}")

