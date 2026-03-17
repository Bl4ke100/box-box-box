import numpy as np
import json
import glob
import os
import multiprocessing

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
    
    # We will just return the list of (tire_type, stint_len) for this driver
    # so we can compute features rapidly for various k_S, k_M, k_H
    
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

# We pre-extract stints for all drivers
race_data = [] # list of (temp, [ (stints_d1, const_d1), (stints_d2, const_d2) ... ])
for race in races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    drivers_info = []
    for d_id in finishing:
        stints, c, temp = get_base_feats(config, strats[d_id])
        drivers_info.append((stints, c))
    race_data.append((config['track_temp'], drivers_info))

def compute_race_features(temp, drivers_info, kS, kM, kH):
    # yields [diff_f], diff_c
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
            
            # effective ages
            k = k_map[tire]
            if length > k:
                # lap ages from k+1 to length
                # effective ages from 1 to length - k
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

def evaluate_thresholds(kS, kM, kH):
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
    
    from scipy.optimize import linprog
    c = np.zeros(10)
    c[9] = -1.0
    A_ext = np.zeros((A.shape[0], 10))
    A_ext[:, :9] = A
    A_ext[:, 9] = 1.0
    b_ub = -C
    bounds = [(None, None)] * 9 + [(0, None)]
    
    res = linprog(c, A_ub=A_ext, b_ub=b_ub, bounds=bounds, method='highs')
    return res

if __name__ == '__main__':
    print(f"Loaded {len(races)} races.")
    # Typical kS, kM, kH.
    # Soft probably 2-10
    # Medium probably 5-20
    # Hard probably 10-30
    options_S = [1, 2, 3, 4, 5, 8, 10]
    options_M = [5, 8, 10, 12, 15]
    options_H = [10, 15, 20, 25]
    
    best_M = -1000
    best_params = None
    best_k = None
    
    for kS in options_S:
        for kM in options_M:
            for kH in options_H:
                res = evaluate_thresholds(kS, kM, kH)
                if res.success:
                    margin = res.x[9]
                    print(f"kS={kS}, kM={kM}, kH={kH} => Feasible! Margin: {margin:.4f}")
                    if margin > best_M:
                        best_M = margin
                        best_params = res.x
                        best_k = (kS, kM, kH)
                else:
                    # Infeasible
                    pass

    if best_params is not None:
        print("Best thresholds:", best_k)
        print("Best params:", best_params)
        with open("thresholds_results.json", "w") as f:
            json.dump({"k": best_k, "params": list(best_params)}, f)
