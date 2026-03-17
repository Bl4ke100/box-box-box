"""
Test different combinations of tie-breaking rules systematically.
"""
import json, glob, os

def load_temp_map():
    with open('temp_map.json') as f:
        return json.load(f)

t_map = load_temp_map()

def get_params(temp):
    t_str = str(temp)
    if t_str in t_map:
        p = t_map[t_str]
    else:
        t_closest = min(t_map.keys(), key=lambda k: abs(int(k) - temp))
        p = t_map[t_closest]
    return {'SOFT': p[0], 'MEDIUM': 0.0, 'HARD': p[1]}, {'SOFT': p[2], 'MEDIUM': p[3], 'HARD': p[4]}

COMPOUND_SPEED = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}  # 0=fastest

def sim_with_tiebreak(file_path, rounding=4, tiebreak='compound_grid'):
    t = json.load(open(file_path))
    config = t['race_config']
    strats = t['strategies']
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    c_offset, deg_rate_c = get_params(temp)
    
    driver_times = []
    for pos, s in strats.items():
        d_id = s['driver_id']
        time = plt * len(s['pit_stops'])
        current_lap = 1
        current_tire = s['starting_tire']
        stints = []
        for stop in s['pit_stops']:
            stints.append((current_tire, stop['lap'] - current_lap + 1))
            current_lap = stop['lap'] + 1
            current_tire = stop['to_tire']
        if current_lap <= total_laps:
            stints.append((current_tire, total_laps - current_lap + 1))
        for tire, slen in stints:
            time += (blt + c_offset[tire]) * slen
            K = max(0, slen - th[tire])
            time += (K*(K+1)/2) * blt * deg_rate_c[tire]
        
        fcs = COMPOUND_SPEED[stints[0][0]]
        last_tire, last_slen = stints[-1]
        last_deg = max(0, last_slen - th[last_tire])
        last_lap = blt + c_offset[last_tire] + last_deg * blt * deg_rate_c[last_tire]
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((time, fcs, last_lap, grid_pos, d_id))
    
    if tiebreak == 'compound_grid':
        driver_times.sort(key=lambda x: (round(x[0], rounding), x[1], x[3]))
    elif tiebreak == 'lastlap_grid':
        driver_times.sort(key=lambda x: (round(x[0], rounding), round(x[2], rounding), x[3]))
    elif tiebreak == 'lastlap_desc_grid':   # bigger last lap = wins
        driver_times.sort(key=lambda x: (round(x[0], rounding), -round(x[2], rounding), x[3]))
    elif tiebreak == 'compound_lastlap_grid':
        driver_times.sort(key=lambda x: (round(x[0], rounding), x[1], round(x[2], rounding), x[3]))
    elif tiebreak == 'compound_lastlap_desc_grid':
        driver_times.sort(key=lambda x: (round(x[0], rounding), x[1], -round(x[2], rounding), x[3]))
    elif tiebreak == 'grid_compound':
        driver_times.sort(key=lambda x: (round(x[0], rounding), x[3], x[1]))
    elif tiebreak == 'pure_grid':
        driver_times.sort(key=lambda x: (round(x[0], rounding), x[3]))
    elif tiebreak == 'pure_grid_noround':
        driver_times.sort(key=lambda x: (x[0], x[3]))
    
    return [x[4] for x in driver_times]

def run_tests(tiebreak, rounding):
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    passed = 0
    for f in test_files:
        name = os.path.basename(f)
        ef = os.path.join(expected_dir, name)
        pred = sim_with_tiebreak(f, rounding=rounding, tiebreak=tiebreak)
        exp = json.load(open(ef))['finishing_positions']
        if pred == exp:
            passed += 1
    return passed

print("Testing different tie-breaking rules:\n")
for tiebreak in ['pure_grid', 'pure_grid_noround', 'lastlap_grid']:
    for rounding in [3, 4, 5]:
        score = run_tests(tiebreak, rounding)
        print(f"  {tiebreak} (round={rounding}): {score}/100")
