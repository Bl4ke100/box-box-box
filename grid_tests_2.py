import os
import glob
import json
import itertools
import multiprocessing

def load_data():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    test_data = []
    
    for f_in in test_files:
        name = os.path.basename(f_in)
        f_exp = os.path.join(expected_dir, name)
        with open(f_in, 'r') as f: t = json.load(f)
        with open(f_exp, 'r') as f: e = json.load(f)
        expected_pos = e['finishing_positions']
        rank_map = {d: i for i, d in enumerate(expected_pos)}
        test_data.append((t, rank_map))
    return test_data

test_data = load_data()

def evaluate(args):
    c_s, c_h, d_s, d_m, d_h = args
    c_offset = {'SOFT': c_s, 'MEDIUM': 0.0, 'HARD': c_h}
    deg_rate = {'SOFT': d_s, 'MEDIUM': d_m, 'HARD': d_h}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    total_error = 0.0
    for t, expected_rank_map in test_data:
        config = t['race_config']
        strats = t['strategies']
        blt = config['base_lap_time']
        plt = config['pit_lane_time']
        temp = config['track_temp']
        total_laps = config['total_laps']
        
        if temp < 25: t_mult = 0.8
        elif temp <= 34: t_mult = 1.0
        else: t_mult = 1.3
            
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
                
            driver_times.append((time, d_id))
            
        driver_times.sort(key=lambda x: x[0])
        
        for true_rank, (time, d_id) in enumerate(driver_times):
            expected_rank = expected_rank_map[d_id]
            total_error += abs(true_rank - expected_rank)
            
    return total_error, args

if __name__ == '__main__':
    cs_range = [-1.006, -1.005, -1.004]
    ch_range = [0.803, 0.804, 0.805]
    ds_range = [0.0197, 0.0198, 0.0199]
    dm_range = [0.0099, 0.0100, 0.0101]
    dh_range = [0.0049, 0.0050, 0.0051]
    
    search_space = list(itertools.product(cs_range, ch_range, ds_range, dm_range, dh_range))
    print(f"Total configs: {len(search_space)}")
    
    best_err = float('inf')
    best_args = None
    
    with multiprocessing.Pool(processes=6) as pool:
        for err, args in pool.imap_unordered(evaluate, search_space):
            if err < best_err:
                best_err = err
                best_args = args
                print(f"New Best! Error: {err} -> Args: {args}")
                
    print(f"Final Best: {best_err} with {best_args}")
