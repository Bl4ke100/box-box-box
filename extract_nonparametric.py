import json
import glob
import os
import numpy as np
from scipy.optimize import linprog

def get_features(config, strat):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    temp = config['track_temp']
    
    if temp < 25: temp_idx = 0
    elif temp <= 34: temp_idx = 1
    else: temp_idx = 2
    
    c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}
    
    # Variables: C_S, C_H (2) + 50*SOFT + 50*MED + 50*HARD = 152 vars
    feats = np.zeros(152)
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
        c_idx = c_idx_map[tire]
        if tire == 'SOFT': feats[0] += slen
        elif tire == 'HARD': feats[1] += slen
        time_const += blt * slen
        
        # Add temperature multiplier to the pure variables?
        # Let's scale the feature extracted by t_mult * blt so the variables are TRUE coefficients!
        t_mult = 0.8 if temp_idx == 0 else 1.0 if temp_idx == 1 else 1.3
        
        for k in range(1, slen + 1):
            if k > 50: k = 50 # Cap at 50 for array size
            feat_idx = 2 + c_idx * 50 + (k - 1)
            feats[feat_idx] += blt * t_mult
            
    return feats, time_const

def main():
    data_dir = r"data/historical_races"
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    
    races = []
    for f in files[:10]: # Load a robust subset
        races.extend(json.load(open(f)))
        
    A_ub = []
    b_ub = []
    
    # We want Time_1 <= Time_2 -> Time_1 - Time_2 <= 0.0
    margin = 0.0
    
    for race in races:
        config = race['race_config']
        strats = race['strategies']
        strat_map = {s['driver_id']: s for s in strats.values()}
        e = race['finishing_positions']
        
        for i in range(len(e) - 1):
            d1, d2 = e[i], e[i+1]
            f1, c1 = get_features(config, strat_map[d1])
            f2, c2 = get_features(config, strat_map[d2])
            
            diff_f = f1 - f2
            diff_c = c2 - c1
            
            A_ub.append(diff_f)
            b_ub.append(diff_c - margin)
            
    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    c_obj = np.zeros(152) # No minimization, just find any feasible curve
    
    bounds = [(-1.000, -1.000), (0.800, 0.800)] + [(0.0, 1.0)] * 150
    
    print(f"Solving nonparametric LP globally with {len(A_ub)} inequalities...")
    res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    if res.success:
        print("FOUND NONPARAMETRIC CURVE!")
        print("C_S:", res.x[0])
        print("C_H:", res.x[1])
        
        soft_deg = res.x[2:52]
        hard_deg = res.x[102:152]
        print("Soft Laps 10-15:", soft_deg[9:15])
        print("Medium Laps 20-25:", res.x[52+19:52+25])
        print("Hard Laps 30-35:", hard_deg[29:35])
        print("Soft Curve:", soft_deg.tolist())
        print("Hard Curve:", hard_deg.tolist())
    else:
        print("Infeasible! Margin is too strict or impossible shape.")

if __name__ == '__main__':
    main()
