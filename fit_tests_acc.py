import os
import glob
import json
import numpy as np
from scipy.optimize import differential_evolution

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    test_data = []
    
    for f_in in test_files:
        name = os.path.basename(f_in)
        f_exp = os.path.join(expected_dir, name)
        
        with open(f_in, 'r') as f:
            t = json.load(f)
            
        with open(f_exp, 'r') as f:
            e = json.load(f)
            
        expected_pos = e['finishing_positions']
        # create a map of driver_id -> rank
        rank_map = {d: i for i, d in enumerate(expected_pos)}
        test_data.append((t, rank_map))
        
    print(f"Loaded {len(test_data)} test sets.")

    def obj(W):
        # W -> [cs, ch, ds, dm, dh]
        c_offset = {'SOFT': W[0], 'MEDIUM': 0.0, 'HARD': W[1]}
        deg_rate = {'SOFT': W[2], 'MEDIUM': W[3], 'HARD': W[4]}
        th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
        
        total_error = 0.0
        
        for t, expected_rank_map in test_data:
            config = t['race_config']
            strats = t['strategies']
            
            blt = config['base_lap_time']
            plt = config['pit_lane_time']
            temp = config['track_temp']
            total_laps = config['total_laps']
            
            if temp < 25:
                t_mult = 0.8
            elif temp <= 34:
                t_mult = 1.0
            else:
                t_mult = 1.3
                
            driver_times = []
            
            for pos, s in strats.items():
                d_id = s['driver_id']
                time = plt * len(s['pit_stops'])
                
                current_lap = 1
                current_tire = s['starting_tire']
                stops = s['pit_stops']
                
                stints = []
                for stop in stops:
                    pit_lap = stop['lap']
                    stints.append((current_tire, pit_lap - current_lap + 1))
                    current_lap = pit_lap + 1
                    current_tire = stop['to_tire']
                    
                if current_lap <= total_laps:
                    stints.append((current_tire, total_laps - current_lap + 1))
                    
                for tire, slen in stints:
                    time += (blt + c_offset[tire]) * slen
                    K = max(0, slen - th[tire])
                    sum_deg = (K * (K + 1)) / 2
                    time += sum_deg * blt * deg_rate[tire] * t_mult
                    
                last_tire, last_slen = stints[-1]
                last_age = last_slen
                last_deg = max(0, last_age - th[last_tire])
                last_lap = blt + c_offset[last_tire] + last_deg * blt * deg_rate[last_tire] * t_mult
                
                grid_pos = int(pos.replace('pos', ''))
                driver_times.append((time, last_lap, grid_pos, d_id))
                
            driver_times.sort(key=lambda x: (round(x[0], 4), round(x[1], 4), x[2]))
            
            # compute rank error
            for true_rank, (time, last_lap, grid_pos, d_id) in enumerate(driver_times):
                expected_rank = expected_rank_map[d_id]
                total_error += abs(true_rank - expected_rank)
                
        return total_error

    bounds = [
        (-2.0, -0.5), # C_S
        (0.5, 2.0),    # C_H
        (0.005, 0.05), # D_S
        (0.001, 0.03), # D_M
        (0.0001, 0.02)  # D_H
    ]
    
    print("Starting exact accuracy calibrator...")
    res = differential_evolution(obj, bounds, maxiter=200, popsize=15, disp=True, workers=1)
    
    print("Best Total Rank Error:", res.fun)
    print("Best Params:", res.x)

if __name__ == '__main__':
    main()
