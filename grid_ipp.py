"""
Grid search over tire IPP thresholds (initial performance period before degradation kicks in).
Previous searches kept fixed at SOFT=10, MEDIUM=20, HARD=30.
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

test_data = load_data()

def sim_race(config, strats, c_s, c_h, d_s, d_m, d_h, th_s, th_m, th_h):
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

def evaluate(args):
    th_s, th_m, th_h = args
    c_s, c_h = -1.0, 0.8
    correct = 0
    for t, expected in test_data:
        config = t['race_config']
        temp = config['track_temp']
        if temp < 25: tmult = 0.8
        elif temp <= 34: tmult = 1.0
        else: tmult = 1.3
        d_s = 0.0198 * tmult
        d_m = 0.01 * tmult
        d_h = 0.005 * tmult
        predicted = sim_race(config, t['strategies'], c_s, c_h, d_s, d_m, d_h, th_s, th_m, th_h)
        if predicted == expected:
            correct += 1
    return correct, args

if __name__ == '__main__':
    # Vary IPP thresholds
    th_s_vals = [8, 9, 10, 11, 12]
    th_m_vals = [18, 19, 20, 21, 22]
    th_h_vals = [28, 29, 30, 31, 32]
    
    search_space = list(itertools.product(th_s_vals, th_m_vals, th_h_vals))
    print(f"Total IPP configs: {len(search_space)}")
    
    best = 0
    best_args = None
    
    with multiprocessing.Pool(processes=6) as pool:
        for correct, args in pool.imap_unordered(evaluate, search_space):
            if correct > best:
                best = correct
                best_args = args
                print(f"New Best! {correct}/100 -> IPP thresholds: {args}")
    
    print(f"\nFinal Best: {best}/100 with IPP={best_args}")
