import numpy as np
from scipy.optimize import linprog
import json
import glob
import os
import itertools
import multiprocessing

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_coefs(race_config, strat, th, p):
    # Returns [C_S, C_M, C_H, D_S, D_M, D_H] + Pit_Penalty_Constant
    coefs = np.zeros(6 + 1)
    
    total_laps = race_config['total_laps']
    plt = race_config['pit_lane_time']
    blt = race_config['base_lap_time']
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    coefs[6] = plt * len(stops)
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stints.append((current_tire, pit_lap - current_lap + 1))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
        
    for tire, slen in stints:
        c_idx = c_idx_map[tire]
        
        # Compound additive offset
        coefs[c_idx] += slen
        
        # Deg multiplier of BLT
        ages = np.arange(1, slen + 1)
        degraded = np.maximum(0, ages - th[c_idx])
        if p == 1:
            penalties = degraded
        else:
            penalties = degraded ** p
            
        coefs[3 + c_idx] += np.sum(penalties) * blt
        
    return coefs

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]
eval_races = valid_races[:80] # 80 races is enough to strictly constrain 6 variables

print("Pre-extracting race pairs...")
race_pairs = []
for race in eval_races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        race_pairs.append((config, strats[d1], strats[d2]))

def check_th(args):
    th_s, th_m, th_h, p = args
    th = [th_s, th_m, th_h]
    
    A_diff = []
    C_diff = []
    
    for config, s1, s2 in race_pairs:
        c1 = get_coefs(config, s1, th, p)
        c2 = get_coefs(config, s2, th, p)
        
        diff = c1 - c2
        diff_f = diff[:6]
        diff_C = diff[6]
        
        if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
            A_diff.append(diff_f)
            C_diff.append(diff_C)
            
    A = np.array(A_diff)
    C = np.array(C_diff)
    
    c = np.zeros(6)
    c[:3] = 0.0001
    c[3:] = 0.0001
    
    # Needs a 0.001 boundary to guarantee strict topological success and avoid degenerate ties
    b_ub = -C - 0.0
    
    # bounds: Compounds (-3 to 3), Deg (0 to None)
    bounds = [(-3.0, 3.0)] * 3 + [(0.0, None)] * 3
    
    res = linprog(c, A_ub=A, b_ub=b_ub, bounds=bounds, method='highs')
    
    if res.success:
        return (th, p, res.x)
    return None

if __name__ == '__main__':
    search_space = []
    # Narrow grid: 
    # S th: 1 to 10
    # M th: 5 to 15
    # H th: 10 to 25
    for p in [1, 2]:
        for s in range(1, 8):
            for m in range(5, 12):
                for h in range(10, 25):
                    search_space.append((s, m, h, p))
                    
    print(f"Total combinations: {len(search_space)}")
    
    # We will use single process map for windows safety, or a small pool
    with multiprocessing.Pool(processes=6) as pool:
        for idx, result in enumerate(pool.imap_unordered(check_th, search_space)):
            if idx % 500 == 0:
                print(f"Searched {idx} combinations...")
            if result is not None:
                print("\nBINGO! FOUND EXACT SOLUTION!")
                print(f"Thresholds: {result[0]}, p={result[1]}")
                print(f"W: {result[2]}")
                pool.terminate()
                break

