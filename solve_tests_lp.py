import json
import glob
import os
import numpy as np
from scipy.optimize import linprog

def get_features(config, strat, th):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    temp = config['track_temp']
    
    if temp < 25: temp_idx = 0
    elif temp <= 34: temp_idx = 1
    else: temp_idx = 2
    
    c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}
    
    # Features:
    # 0: C_S
    # 1: C_H
    # 2: Deg_S_Cold, 3: Deg_M_Cold, 4: Deg_H_Cold
    # 5: Deg_S_Warm, 6: Deg_M_Warm, 7: Deg_H_Warm
    # 8: Deg_S_Hot,  9: Deg_M_Hot, 10: Deg_H_Hot
    
    feats = np.zeros(11)
    time_const = plt * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stints.append((current_tire, pit_lap - current_lap + 1))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
        
    for tire, slen in stints:
        if tire == 'SOFT': feats[0] += slen
        elif tire == 'HARD': feats[1] += slen
        time_const += blt * slen # MEDIUM C_M = 0
        
        K = max(0, slen - th[tire])
        sum_deg = (K * (K + 1)) / 2
        
        deg_feat_idx = 2 + temp_idx * 3 + c_idx_map[tire]
        feats[deg_feat_idx] += sum_deg * blt
        
    return feats, time_const

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    A_ub = []
    b_ub = []
    
    for f_in in test_files:
        name = os.path.basename(f_in)
        f_exp = os.path.join(expected_dir, name)
        
        with open(f_in, 'r') as f: t = json.load(f)
        with open(f_exp, 'r') as f: e = json.load(f)['finishing_positions']
        
        config = t['race_config']
        strats = t['strategies']
        strat_map = {s['driver_id']: s for s in strats.values()}
        
        for i in range(len(e) - 1):
            d1 = e[i]
            d2 = e[i+1]
            
            f1, c1 = get_features(config, strat_map[d1], th)
            f2, c2 = get_features(config, strat_map[d2], th)
            
            # Time(d1) <= Time(d2)
            # f1*W + c1 <= f2*W + c2
            # (f1 - f2)*W <= c2 - c1
            
            # We want strict inequality to prevent ties that shouldn't tie!
            # But wait! Some exact ties DO exist and use Grid Pos tie-breaker!
            # To handle Grid Pos tie-breaker:
            grid1 = int([k for k, v in strats.items() if v['driver_id'] == d1][0].replace('pos', ''))
            grid2 = int([k for k, v in strats.items() if v['driver_id'] == d2][0].replace('pos', ''))
            
            diff_f = f1 - f2
            diff_c = c2 - c1
            
            diff_f = f1 - f2
            diff_c = c2 - c1
            A_ub.append(diff_f)
            b_ub.append(diff_c)

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    c = np.zeros(11)
    
    # bounds
    bounds = [
        (-1.1, -0.9), # C_S
        (0.7, 0.9),   # C_H
    ]
    # Deg params > 0
    bounds += [(0.001, 0.05)] * 9

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    if res.success:
        print("FOUND PERFECT EXACT FLOATS!")
        print("C_S:", res.x[0])
        print("C_H:", res.x[1])
        print("Deg_Cold [S, M, H]:", res.x[2:5])
        print("Deg_Warm [S, M, H]:", res.x[5:8])
        print("Deg_Hot  [S, M, H]:", res.x[8:11])
    else:
        print("Infeasible!")

if __name__ == '__main__':
    main()
