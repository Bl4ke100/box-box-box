"""
Grid search over temperature thresholds AND parameters simultaneously.
The key question: are the thresholds at <25 and >34 or different values?
"""
import json, glob, os, itertools, multiprocessing

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
        test_data.append((t, e['finishing_positions']))
    return test_data

def sim_race(config, strats, c_s, c_h, d_s, d_m, d_h, th_s=10, th_m=20, th_h=30):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    c_offset = {'SOFT': c_s, 'MEDIUM': 0.0, 'HARD': c_h}
    deg_rate = {'SOFT': d_s, 'MEDIUM': d_m, 'HARD': d_h}
    th = {'SOFT': th_s, 'MEDIUM': th_m, 'HARD': th_h}
    driver_times = []
    for pos, s in strats.items():
        d_id = s['driver_id']
        time = plt * len(s['pit_stops'])
        current_lap = 1
        current_tire = s['starting_tire']
        stints = []
        for stop in s['pit_stops']:
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
            time += sum_deg * blt * deg_rate[tire]
        driver_times.append((time, int(d_id.replace('D', '')), d_id))
    driver_times.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in driver_times]

test_data = load_data()

def evaluate(args):
    c_s, c_h, d_s_base, d_m_base, d_h_base, t_cold, t_hot, t_mult_cold, t_mult_hot = args
    correct = 0
    for t, expected in test_data:
        config = t['race_config']
        temp = config['track_temp']
        if temp < t_cold: tmult = t_mult_cold
        elif temp >= t_hot: tmult = t_mult_hot
        else: tmult = 1.0
        d_s = d_s_base * tmult
        d_m = d_m_base * tmult
        d_h = d_h_base * tmult
        predicted = sim_race(config, t['strategies'], c_s, c_h, d_s, d_m, d_h)
        if predicted == expected:
            correct += 1
    return correct, args

if __name__ == '__main__':
    # Fixed best params from previous search: c_s=-1.0, c_h=0.8, base_ds=0.0198, base_dm=0.01, base_dh=0.005
    # Vary threshold boundaries and multipliers
    c_s_vals  = [-1.0]
    c_h_vals  = [0.8]
    ds_vals   = [0.0196, 0.0197, 0.0198, 0.0199, 0.0200]
    dm_vals   = [0.0099, 0.0100, 0.0101]
    dh_vals   = [0.0049, 0.0050, 0.0051]
    t_cold_vals = [22, 23, 24, 25, 26]   # Below this = cold
    t_hot_vals  = [33, 34, 35, 36]        # At/above this = hot
    mult_cold_vals = [0.75, 0.78, 0.80, 0.82, 0.85]
    mult_hot_vals  = [1.25, 1.28, 1.30, 1.32, 1.35]
    
    search_space = list(itertools.product(
        c_s_vals, c_h_vals, ds_vals, dm_vals, dh_vals,
        t_cold_vals, t_hot_vals, mult_cold_vals, mult_hot_vals
    ))
    print(f"Total configs: {len(search_space)}")
    
    best = 0
    best_args = None
    
    with multiprocessing.Pool(processes=6) as pool:
        for correct, args in pool.imap_unordered(evaluate, search_space, chunksize=10):
            if correct > best:
                best = correct
                best_args = args
                print(f"New Best! {correct}/100 -> c_s={args[0]}, c_h={args[1]}, ds={args[2]}, dm={args[3]}, dh={args[4]}, t_cold<{args[5]}, t_hot>={args[6]}, mult_cold={args[7]}, mult_hot={args[8]}")
                if correct == 100:
                    print("PERFECT!")
                    break
    
    print(f"\nFinal Best: {best}/100")
    print(f"Args: {best_args}")
