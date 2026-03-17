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
        time_const += blt * slen
        
        K = max(0, slen - th[tire])
        sum_deg = (K * (K + 1)) / 2
        
        deg_feat_idx = 2 + temp_idx * 3 + c_idx_map[tire]
        feats[deg_feat_idx] += sum_deg * blt
        
    return feats, time_const

def main():
    data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    
    races = []
    for f in files[:8]: # 8 files * 250 = 2000 races
        races.extend(json.load(open(f)))
        
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    A_ub = []
    b_ub = []
    
    for race in races:
        config = race['race_config']
        strats = race['strategies']
        strat_map = {s['driver_id']: s for s in strats.values()}
        e = race['finishing_positions']
        
        for i in range(len(e) - 1):
            d1 = e[i]
            d2 = e[i+1]
            
            f1, c1 = get_features(config, strat_map[d1], th)
            f2, c2 = get_features(config, strat_map[d2], th)
            
            diff_f = f1 - f2
            diff_c = c2 - c1
            
            A_ub.append(diff_f)
            b_ub.append(diff_c) # <= 0 difference!
            
    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    # We construct objective function to regularize scalars around our known approximate vector to prevent degeneracy!
    # Because we use <=, 0 is a trivial solution if boundaries permit!
    c_obj = np.zeros(11)
    # Actually if we set bounds tight around 1.0 and 0.8 it can't be 0!
    bounds = [
        (-1.05, -0.95), # C_S
        (0.75, 0.85),   # C_H
        (0.015, 0.025), # Deg_Cold_S
        (0.005, 0.015), # Deg_Cold_M
        (0.001, 0.010), # Deg_Cold_H
        (0.015, 0.025), # Deg_Warm_S
        (0.005, 0.015), # Deg_Warm_M
        (0.001, 0.010), # Deg_Warm_H
        (0.015, 0.035), # Deg_Hot_S
        (0.005, 0.025), # Deg_Hot_M
        (0.001, 0.010), # Deg_Hot_H
    ]
    
    print(f"Solving LP with {len(A_ub)} inequalities...")
    res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    if res.success:
        print("FOUND PERFECT EXACT HISTORICAL FLOATS!")
        print("C_S:", res.x[0])
        print("C_H:", res.x[1])
        print("Deg_Cold [S, M, H]:", res.x[2:5])
        print("Deg_Warm [S, M, H]:", res.x[5:8])
        print("Deg_Hot  [S, M, H]:", res.x[8:11])
        
        with open("lp_res.json", "w") as f:
            json.dump(res.x.tolist(), f)
    else:
        print("Infeasible! The formula shape is structurally incorrect!")

if __name__ == '__main__':
    main()
