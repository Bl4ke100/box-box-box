"""
For each temperature, solve LP to MAXIMIZE degradation (push towards the upper boundary of what's feasible).
Use much more historical data (all 30k races) for tight bounds.
"""
import json
import glob
import os
import numpy as np
from scipy.optimize import linprog

def get_features(config, strat, th):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    
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
    races = [r for r in all_races if r['race_config']['track_temp'] == T][:500]
    if len(races) < 5: return None
    
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    A_ub = []
    b_ub = []
    
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
            b_ub.append(c2 - c1)

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    bounds = [
        (-1.20, -0.80),  # C_S
        (0.60, 1.00),    # C_H
        (0.010, 0.035),  # D_S
        (0.005, 0.020),  # D_M
        (0.001, 0.015)   # D_H
    ]
    
    results = {}
    
    # Try multiple objectives to find a central solution
    objectives_and_names = [
        (np.array([0, 0, -1, 0, 0]), 'max_D_S'),
        (np.array([0, 0, 1, 0, 0]), 'min_D_S'),
        (np.array([0, 0, 0, 0, -1]), 'max_D_H'),  
        (np.array([0, 0, -1, -1, -1]), 'max_all_deg'),
        (np.array([0, 0, 1, 1, 1]), 'min_all_deg'),
    ]
    
    for c_obj, name in objectives_and_names:
        res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        if res.success:
            results[name] = res.x.tolist()
    
    return results

def main():
    data_dir = r"data/historical_races"
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    races = []
    for f in files[:60]:  # 60 files * 250 = 15,000 races for better constraints
        try:
            races.extend(json.load(open(f)))
        except:
            pass
    
    print(f"Loaded {len(races)} historical races")
    
    temps = sorted(list(set([r['race_config']['track_temp'] for r in races])))
    all_results = {}
    
    for T in temps:
        res = get_for_temp(T, races)
        if res:
            all_results[T] = res
            # Report max vs min D_S spread
            if 'max_D_S' in res and 'min_D_S' in res:
                spread = res['max_D_S'][2] - res['min_D_S'][2]
                print(f"T={T}: D_S range [{res['min_D_S'][2]:.5f}, {res['max_D_S'][2]:.5f}] spread={spread:.5f}")
        else:
            print(f"T={T}: Failed")
    
    with open("temp_map_maxdeg.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Saved to temp_map_maxdeg.json")

if __name__ == '__main__':
    main()
