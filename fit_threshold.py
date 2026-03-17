import numpy as np
from scipy.optimize import differential_evolution
import json
import glob
import os

def main():
    data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
    files = glob.glob(os.path.join(data_dir, "*.json"))

    races = []
    for f in files[:8]:
        with open(f, 'r') as fin:
            races.extend(json.load(fin))

    eval_races = races[:200]

    def loss(W):
        # W -> [base_M, base_H, deg_S, deg_M, deg_H, temp_S, temp_M, temp_H, thresh_S, thresh_M, thresh_H]
        base_M, base_H = W[0], W[1]
        deg_S, deg_M, deg_H = W[2], W[3], W[4]
        tmp_S, tmp_M, tmp_H = W[5], W[6], W[7]
        th_S, th_M, th_H = W[8], W[9], W[10]
        
        # Round thresholds to nearest integer? Let's just let the solver use floats and we will interpret.
        # F1 laps are discrete, so threshold is likely an integer, but we can evaluate as float for gradients.
        
        bases = [0.0, base_M, base_H]
        degs = [deg_S, deg_M, deg_H]
        tmps = [tmp_S, tmp_M, tmp_H]
        ths = [th_S, th_M, th_H]
        
        violations = 0
        total_margin = 0.0
        
        for race in eval_races:
            config = race['race_config']
            strats = {s['driver_id']: s for _, s in race['strategies'].items()}
            finishing = race['finishing_positions']
            
            temp = config['track_temp']
            plt = config['pit_lane_time']
            blt = config['base_lap_time']
            total_laps = config['total_laps']
            
            times = []
            
            for d in finishing:
                strat = strats[d]
                
                # Base time
                time = blt * total_laps + plt * len(strat['pit_stops'])
                
                current_lap = 1
                current_tire = strat['starting_tire']
                stops = strat['pit_stops']
                
                stints = []
                for stop in stops:
                    pit_lap = stop['lap']
                    stint_len = pit_lap - current_lap + 1
                    stints.append((current_tire, stint_len))
                    current_lap = pit_lap + 1
                    current_tire = stop['to_tire']
                    
                if current_lap <= total_laps:
                    stints.append((current_tire, total_laps - current_lap + 1))
                    
                for tire, slen in stints:
                    idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
                    
                    time += bases[idx] * slen
                    
                    # Apply degradation
                    # For each lap i from 1 to slen:
                    # diff = max(0, i - ths[idx])
                    # deg_time = diff * degs[idx] * (1 + temp * tmps[idx])
                    
                    # We can compute sum without loop
                    th = ths[idx]
                    int_th = int(th)
                    if slen > int_th:
                        n = slen - int_th
                        sum_diff = n * (n + 1) / 2
                        
                        # maybe there's a fractional part? DE will just push it to nearest int anyway.
                        # What if the TEMP multiplier is additive or multiplicative?
                        # Let's assume multiplier: (1 + temp * tmps[idx])
                        time += sum_diff * degs[idx] * (1 + temp * tmps[idx])
                        
                times.append(time)
                
            for i in range(len(times) - 1):
                diff = times[i] - times[i+1]
                if diff > -0.0001:
                    violations += 1
                    total_margin += diff
                    
        return violations + total_margin * 0.01

    bounds = [
        (0.5, 3.0), (1.0, 3.5), # base M, H
        (0.01, 0.5), (0.01, 0.3), (0.001, 0.15), # deg S, M, H
        (-0.05, 0.05), (-0.05, 0.05), (-0.05, 0.05), # temp S, M, H
        (1, 15), (5, 25), (10, 40) # threshold S, M, H
    ]

    print("Starting DE solver with threshold laps...")
    res = differential_evolution(loss, bounds, maxiter=200, workers=1, popsize=20, disp=True)

    print("Best loss:", res.fun)
    print("Best W:", res.x)

if __name__ == '__main__':
    main()
