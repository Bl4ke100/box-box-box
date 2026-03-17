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
        # W -> [base_M, base_H, deg_S, deg_M, deg_H, pow_S, pow_M, pow_H, tmp_S, tmp_M, tmp_H]
        base_M, base_H = W[0], W[1]
        deg_S, deg_M, deg_H = W[2], W[3], W[4]
        pow_S, pow_M, pow_H = W[5], W[6], W[7]
        tmp_S, tmp_M, tmp_H = W[8], W[9], W[10]
        
        bases = [0.0, base_M, base_H]
        degs = [deg_S, deg_M, deg_H]
        pows = [pow_S, pow_M, pow_H]
        tmps = [tmp_S, tmp_M, tmp_H]
        
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
                
                time = blt * total_laps + plt * len(strat['pit_stops'])
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
                    idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
                    time += bases[idx] * slen
                    
                    # deg_time = age^power * deg * (1 + temp*tmp)
                    ages = np.arange(1, slen + 1)
                    sum_deg = np.sum(ages ** pows[idx])
                    time += sum_deg * degs[idx] * (1.0 + temp * tmps[idx])
                        
                times.append(time)
                
            for i in range(len(times) - 1):
                diff = times[i] - times[i+1]
                if diff > -0.0001:
                    violations += 1
                    total_margin += diff
                    
        return violations + total_margin * 0.01

    bounds = [
        (0.5, 3.0), (1.0, 4.0), # base M, H
        (0.01, 0.5), (0.01, 0.5), (0.01, 0.5), # deg S, M, H
        (1.0, 3.0), (1.0, 3.0), (1.0, 3.0), # power S, M, H
        (-0.02, 0.05), (-0.02, 0.05), (-0.02, 0.05) # temp S, M, H
    ]

    print("Starting DE solver for Exponent Power...")
    res = differential_evolution(loss, bounds, maxiter=200, workers=1, popsize=20, disp=True)

    print("Best loss:", res.fun)
    print("Best W:", res.x)

if __name__ == '__main__':
    main()
