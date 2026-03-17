"""
With lastlap_grid (67/100), analyze the remaining 33 failures in detail.
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

def sim(file_path):
    t = json.load(open(file_path))
    config = t['race_config']
    strats = t['strategies']
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    c_offset, deg_rate_c = get_params(temp)
    
    driver_data = []
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
        
        last_tire, last_slen = stints[-1]
        last_deg = max(0, last_slen - th[last_tire])
        last_lap = blt + c_offset[last_tire] + last_deg * blt * deg_rate_c[last_tire]
        grid_pos = int(pos.replace('pos', ''))
        driver_data.append({'d_id': d_id, 'time': time, 'last_lap': last_lap, 'grid': grid_pos, 'stints': stints})
    
    driver_data.sort(key=lambda x: (round(x['time'], 4), round(x['last_lap'], 4), x['grid']))
    return [x['d_id'] for x in driver_data], driver_data

test_cases_dir = r"data/test_cases/inputs"
expected_dir = r"data/test_cases/expected_outputs"
test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))

for f in test_files:
    name = os.path.basename(f)
    ef = os.path.join(expected_dir, name)
    pred, data = sim(f)
    exp = json.load(open(ef))['finishing_positions']
    if pred != exp:
        t = json.load(open(f))
        temp = t['race_config']['track_temp']
        # Find first point of divergence
        diffs = [(i, exp[i], pred[i]) for i in range(20) if exp[i] != pred[i]]
        if diffs:
            pos, exp_d, got_d = diffs[0]
            d1 = next(x for x in data if x['d_id'] == exp_d)
            d2 = next(x for x in data if x['d_id'] == got_d)
            time_tie = abs(d1['time'] - d2['time']) < 1e-8
            last_tie = abs(d1['last_lap'] - d2['last_lap']) < 1e-8 if time_tie else False
            print(f"{name} (T={temp}): {exp_d}(grid={d1['grid']}) vs {got_d}(grid={d2['grid']})")
            print(f"  Time tie: {time_tie}, LastLap tie: {last_tie}")
            if time_tie:
                print(f"  {exp_d} stints: {d1['stints']}, last_lap={d1['last_lap']:.6f}, grid={d1['grid']}")
                print(f"  {got_d} stints: {d2['stints']}, last_lap={d2['last_lap']:.6f}, grid={d2['grid']}")
