"""
Fine-grained grid search — evaluate_stepped at module level for multiprocessing.
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

def sim_race(config, strats, c_offset, deg_rate, th):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
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

# Pre-load at module level so workers can access
test_data = load_data()

def evaluate_stepped(args):
    c_s, c_h, d_s_base, d_m_base, d_h_base = args
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    correct = 0
    for t, expected in test_data:
        config = t['race_config']
        temp = config['track_temp']
        if temp < 25: tmult = 0.8
        elif temp <= 34: tmult = 1.0
        else: tmult = 1.3
        c_offset = {'SOFT': c_s, 'MEDIUM': 0.0, 'HARD': c_h}
        deg_rate = {'SOFT': d_s_base * tmult, 'MEDIUM': d_m_base * tmult, 'HARD': d_h_base * tmult}
        predicted = sim_race(config, t['strategies'], c_offset, deg_rate, th)
        if predicted == expected:
            correct += 1
    return correct, args

if __name__ == '__main__':
    # Near LP values: C_S~-1.0, C_H~0.800, D_S_base~0.0198, D_M_base~0.01004, D_H_base~0.00506
    cs_range = [round(-1.0 + x * 0.001, 4) for x in range(-5, 6)]   # -1.005 to -0.995
    ch_range = [round(0.800 + x * 0.001, 4) for x in range(-5, 6)]  # 0.795 to 0.805
    ds_range = [round(0.0194 + x * 0.0001, 5) for x in range(9)]    # 0.0194 to 0.0202
    dm_range = [round(0.0098 + x * 0.0001, 5) for x in range(7)]    # 0.0098 to 0.0104
    dh_range = [round(0.0048 + x * 0.0001, 5) for x in range(7)]    # 0.0048 to 0.0054
    
    search_space = list(itertools.product(cs_range, ch_range, ds_range, dm_range, dh_range))
    print(f"Total configs: {len(search_space)}")
    
    best = 0
    best_args = None
    
    with multiprocessing.Pool(processes=6) as pool:
        for correct, args in pool.imap_unordered(evaluate_stepped, search_space, chunksize=20):
            if correct > best:
                best = correct
                best_args = args
                print(f"New Best! {correct}/100 -> {args}")
                if correct == 100:
                    print("PERFECT!")
                    break
    
    print(f"\nFinal Best: {best}/100 with {best_args}")
