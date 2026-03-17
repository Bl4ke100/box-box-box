import numpy as np
from scipy.optimize import linprog
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:4]: # Use 4 races to make grid search extremely fast
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
                # lap ages from k+1 to length meaning effective age increments
                # wait! "After this period, degradation effects become noticeable"
                # If k=5, on lap 6, is age=6 or is effective_age=1?
                # "Fresh tires start at age 0. The first lap is driven at age 1."
                # If deg is 0 for first k laps:
                # Approach A: Age is just max(0, actual_age - k). So L6 has age 1. L7 has age 2.
                # Approach B: Age continues to increment, but multiplier is 0 until k. So L6 has age 6.
                # Let's test Approach B first, since "tire age increments by 1".
                # Sum of ages from k+1 to length:
                
                # Approach B:
                ages = np.arange(k + 1, length + 1)
                sum_eff_age = np.sum(ages)
                
                # Approach A:
                # n = length - k
                # sum_eff_age = n * (n + 1) / 2
                
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

def eval_linprog(kS, kM, kH):
    A_diff = []
    C_diff = []
    
    for temp, drivers_info in race_data:
        df, dc = compute_race_features(temp, drivers_info, kS, kM, kH)
        for d_f, d_c in zip(df, dc):
            if any(abs(v) > 0.001 for v in d_f):
                A_diff.append(d_f)
                C_diff.append(d_c)
                
    if not A_diff:
        return False, None
        
    A = np.array(A_diff)
    C = np.array(C_diff)
    
    # We want to find A * W <= -C - M
    c_obj = np.zeros(10)
    c_obj[9] = -1.0
    
    A_ext = np.zeros((A.shape[0], 10))
    A_ext[:, :9] = A
    A_ext[:, 9] = 1.0
    
    bounds = [(0, 10)] * 9 + [(0, 1.0)] # Bound W to prevent unbounded failure!! Maximize M up to 1.0!
    bounds[0] = (0, 0) # S_base = 0
    bounds[1] = (0.5, 3.0)
    bounds[2] = (1.0, 5.0)
    
    res = linprog(c_obj, A_ub=A_ext, b_ub=-C, bounds=bounds, method='highs')
    
    if res.success and res.x[9] > 0.0001:
        return True, res.x
    return False, None

if __name__ == '__main__':
    print("Testing Approach B (Age continues to increment, but degradation is 0 until lap k)")
    # We know Soft degrades fastest. kS should be smallest.
    # Soft probably 1-5, Medium 3-15, Hard 10-25
    options_S = [1, 2, 3, 4]
    options_M = [5, 8, 10, 12, 15]
    options_H = [15, 20, 22, 25, 30]
    
    for kS in options_S:
        for kM in options_M:
            for kH in options_H:
                success, w = eval_linprog(kS, kM, kH)
                if success:
                    print(f"\nBINGO EXACT SOLUTION FOUND! kS={kS}, kM={kM}, kH={kH}")
                    print(f"Margin: {w[-1]}")
                    print(f"W: {w[:9]}")
                    break
