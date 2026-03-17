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
        # W -> [cs, cm, ch, ds, dm, dh, ts, tm, th, tmp, p]
        c_add = [W[0], W[1], W[2]] # ADDITIVE!
        deg = [W[3], W[4], W[5]]
        th = [W[6], W[7], W[8]]
        tmp_scale = W[9]
        p = W[10]
        
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
            
            t_mult = 1.0 + tmp_scale * temp
            
            for d in finishing:
                strat = strats[d]
                
                time = plt * len(strat['pit_stops'])
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
                    
                    time += c_add[idx] * slen # ADDITIVE: independent of BLT
                    
                    ages = np.arange(1, slen + 1)
                    degraded_ages = np.maximum(0, ages - th[idx])
                    
                    if np.any(degraded_ages > 0):
                        penalties = deg[idx] * blt * t_mult * (degraded_ages ** p)
                        time += np.sum(penalties)
                        
                times.append(time)
                
            for i in range(len(times) - 1):
                diff = times[i] - times[i+1]
                if diff > -0.0001:
                    violations += 1
                    total_margin += diff
                    
        return violations + total_margin * 0.01

    bounds = [
        (-3.0, 1.0), (-2.0, 2.0), (0.0, 4.0), # cs, cm, ch (ADDITIVE!)
        (0.000001, 0.05), (0.000001, 0.05), (0.000001, 0.05), # deg s, m, h
        (1.0, 15.0), (3.0, 25.0), (10.0, 40.0), # thresholds
        (-0.02, 0.05), # temp scale
        (1.0, 3.0) # power p
    ]

    print("Starting exact Reverse Hybrid Equation DE solver...")
    res = differential_evolution(loss, bounds, maxiter=200, workers=1, popsize=20, disp=True)

    print("Best loss:", res.fun)
    print("Best W:", res.x)

if __name__ == '__main__':
    main()
