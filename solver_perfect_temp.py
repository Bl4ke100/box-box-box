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

c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_coefs(race_config, strat, th):
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
        coefs[c_idx] += slen
        
        ages = np.arange(1, slen + 1)
        degraded = np.maximum(0, ages - th[c_idx])
        penalties = degraded
        coefs[3 + c_idx] += np.sum(penalties) * blt
        
    return coefs

def solve_for_temp(T):
    valid_races = [r for r in races if r['race_config']['track_temp'] == T]
    eval_races = valid_races[:100] 
    if len(eval_races) < 5:
        print(f"Not enough races for Temp={T}")
        return

    th = [10, 20, 30]

    A_diff = []
    C_diff = []

    for race in eval_races:
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        
        for i in range(len(finishing) - 1):
            d1 = finishing[i]
            d2 = finishing[i+1]
            
            c1 = get_coefs(config, strats[d1], th)
            c2 = get_coefs(config, strats[d2], th)
            
            diff = c1 - c2
            diff_f = diff[:6]
            diff_C = diff[6]
            
            if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
                A_diff.append(diff_f)
                C_diff.append(diff_C)
                
    A = np.array(A_diff)
    C = np.array(C_diff)

    c_obj = np.zeros(6)
    c_obj[:3] = 0.000001
    c_obj[3:] = 0.000001

    A_eq = np.zeros((1, 6))
    A_eq[0, 1] = 1.0 # Force C_M = 0
    b_eq = np.array([0.0])
    
    b_ub = -C

    bounds = [(-3.0, 3.0)] * 3 + [(0.0, None)] * 3

    res = linprog(c_obj, A_ub=A, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if res.success:
        np.set_printoptions(suppress=True, precision=6)
        print(f"\nSUCCESS on Temp={T}!")
        print("C_S, C_M, C_H:", res.x[:3])
        print("D_S, D_M, D_H:", res.x[3:])
    else:
        print(f"\nFAILED on Temp={T}")

solve_for_temp(20)
solve_for_temp(40)
