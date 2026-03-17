import json
import glob
import os
import numpy as np
from scipy.optimize import linprog

def get_features(config, strat, th):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    
    # Vars: C_S(0), C_H(1), D_S(2), D_M(3), D_H(4)
    # C_M is 0.0
    c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}
    
    feats = np.zeros(5)
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
        
        c_i = c_idx_map[tire]
        feats[2 + c_i] += sum_deg * blt
        
    return feats, time_const

def get_for_temp(T, all_races):
    races = [r for r in all_races if r['race_config']['track_temp'] == T][:100]
    if len(races) < 5: return None
    
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    A_ub = []
    b_ub = []
    
    # We add an objective function to strictly minimize magnitude to prevent degeneracy, but constrained around true bounds.
    for race in races:
        config = race['race_config']
        strats = race['strategies']
        strat_map = {s['driver_id']: s for s in strats.values()}
        e = race['finishing_positions']
        
        for i in range(len(e) - 1):
            d1, d2 = e[i], e[i+1]
            f1, c1 = get_features(config, strat_map[d1], th)
            f2, c2 = get_features(config, strat_map[d2], th)
            
            A_ub.append(f1 - f2)
            b_ub.append(c2 - c1) # Weak inequality, exact math tie resolves through chronological engine tie-breakers

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    bounds = [
        (-1.20, -0.80), # C_S
        (0.60, 1.00),   # C_H
        (0.010, 0.035), # D_S
        (0.005, 0.020), # D_M
        (0.001, 0.015)  # D_H
    ]
    # Maximize distance between Deg constants instead of zeros to break degeneracy
    c_obj = np.array([0.0, 0.0, -1.0, 1.0, 1.0]) 
    
    res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if res.success: return res.x
    return None

def main():
    data_dir = r"data/historical_races"
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    races = []
    for f in files[:20]: races.extend(json.load(open(f)))
    
    temps = sorted(list(set([r['race_config']['track_temp'] for r in races])))
    res_map = {}
    for T in temps:
        sol = get_for_temp(T, races)
        if sol is not None:
            res_map[T] = sol.tolist()
            print(f"T={T}: {np.round(sol, 5)}")
        else:
            print(f"T={T} Failed")
            
    with open("temp_map.json", "w") as f: json.dump(res_map, f, indent=2)

if __name__ == '__main__': main()
