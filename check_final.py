"""
Identify which 2 tests still fail, and try broader 5-param search via lap-by-lap.
"""
import json, glob, os, itertools, multiprocessing

test_data = []
for f in sorted(glob.glob(r"data/test_cases/inputs/test_*.json")):
    name = os.path.basename(f)
    t = json.load(open(f))
    exp = json.load(open(os.path.join(r"data/test_cases/expected_outputs", name)))['finishing_positions']
    test_data.append((name, t, exp))

def sim(config, strats, c_s, c_h, d_s, d_m, d_h):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25: tmult = 0.8
    elif temp <= 34: tmult = 1.0
    else: tmult = 1.3
    
    c_offset = {'SOFT': c_s, 'MEDIUM': 0.0, 'HARD': c_h}
    deg_rate = {'SOFT': d_s * tmult, 'MEDIUM': d_m * tmult, 'HARD': d_h * tmult}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    driver_times = []
    for pos, s in strats.items():
        d_id = s['driver_id']
        current_tire = s['starting_tire']
        current_age = 1
        pit_laps = {stop['lap']: stop['to_tire'] for stop in s['pit_stops']}
        total_time = plt * len(s['pit_stops'])
        for lap in range(1, total_laps + 1):
            deg = max(0, current_age - th[current_tire])
            total_time += blt + c_offset[current_tire] + deg * blt * deg_rate[current_tire]
            if lap in pit_laps:
                current_tire = pit_laps[lap]
                current_age = 1
            else:
                current_age += 1
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((total_time, grid_pos, d_id))
    
    driver_times.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in driver_times]

# First: see which tests fail with best params
d_s, d_m, d_h = 0.019775, 0.010003, 0.005055
c_s, c_h = -1.0, 0.8

print("Failing tests with best params:")
for name, t, exp in test_data:
    pred = sim(t['race_config'], t['strategies'], c_s, c_h, d_s, d_m, d_h)
    if pred != exp:
        diffs = [(i, exp[i], pred[i]) for i in range(20) if exp[i] != pred[i]][:3]
        print(f"  {name} (T={t['race_config']['track_temp']}): {diffs}")
