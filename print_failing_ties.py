import os
import glob
import json

def get_times(t):
    config = t['race_config']
    strats = t['strategies']
    
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25: t_mult = 0.8
    elif temp <= 34: t_mult = 1.0
    else: t_mult = 1.3
        
    c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}
    deg_rate = {'SOFT': 0.02, 'MEDIUM': 0.01, 'HARD': 0.005}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
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
            
        driver_times.append((time, d_id, s))
        
    driver_times.sort(key=lambda x: round(x[0], 5))
    return driver_times

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    for test_file in test_files:
        name = os.path.basename(test_file)
        expected_file = os.path.join(expected_dir, name)
        if not os.path.exists(expected_file): continue
            
        with open(test_file, 'r') as f: t = json.load(f)
        with open(expected_file, 'r') as f: expected = json.load(f)['finishing_positions']
        
        d_times = get_times(t)
        predicted = [dt[1] for dt in d_times]
        
        if expected != predicted:
            print(f"\n[{name}] FAILED")
            # find swaps
            for i in range(20):
                if expected[i] != predicted[i]:
                    d_exp = expected[i]
                    d_got = predicted[i]
                    # Find info for d_exp
                    dt_exp = next(dt for dt in d_times if dt[1] == d_exp)
                    dt_got = next(dt for dt in d_times if dt[1] == d_got)
                    
                    if dt_exp[0] == dt_got[0]: # Wait, exact tie?
                        print(f"  SWAP DETECTED: {d_exp} and {d_got}")
                        print(f"    {d_exp} Time: {dt_exp[0]:.6f} | Strat: {dt_exp[2]['starting_tire']} -> {dt_exp[2]['pit_stops']}")
                        print(f"    {d_got} Time: {dt_got[0]:.6f} | Strat: {dt_got[2]['starting_tire']} -> {dt_got[2]['pit_stops']}")
                        break # Only print first swap condition per race

if __name__ == '__main__':
    main()
