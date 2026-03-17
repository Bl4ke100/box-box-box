"""
For each failing test, print the exact computed times for the swapped drivers.
This helps us determine if parameters need adjusting.
"""
import json, glob, os

def load_temp_map():
    with open('temp_map.json') as f:
        return json.load(f)

t_map = load_temp_map()

def get_times(t_data, file_path=None):
    config = t_data['race_config']
    strats = t_data['strategies']
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']

    t_str = str(temp)
    if t_str not in t_map:
        t_closest = min(t_map.keys(), key=lambda k: abs(int(k) - temp))
        params = t_map[t_closest]
    else:
        params = t_map[t_str]

    c_offset = {'SOFT': params[0], 'MEDIUM': 0.0, 'HARD': params[1]}
    deg_rate_c = {'SOFT': params[2], 'MEDIUM': params[3], 'HARD': params[4]}
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
            time += sum_deg * blt * deg_rate_c[tire]

        driver_times.append((time, d_id, s))

    driver_times.sort(key=lambda x: (round(x[0], 4), int(x[1].replace('D', ''))))
    return driver_times

# Focus on test_006 (T=42) - D003 vs D018 swap at position 14
t6 = json.load(open('data/test_cases/inputs/test_006.json'))
exp6 = json.load(open('data/test_cases/expected_outputs/test_006.json'))['finishing_positions']
dt6 = get_times(t6)
print("test_006.json (T=42):")
print("Expected pos 14:", exp6[13], "got pos 14:", dt6[13][1])

d_exp14 = next(d for d in dt6 if d[1] == 'D003')
d_got14 = next(d for d in dt6 if d[1] == 'D018')
print(f"  D003 time: {d_exp14[0]:.6f} stints={[(x[0], x[1]) for x in d_exp14[2]['pit_stops']]}")
print(f"  D018 time: {d_got14[0]:.6f} stints={[(x[0], x[1]) for x in d_got14[2]['pit_stops']]}")
print(f"  D003 starts: {d_exp14[2]['starting_tire']}")
print(f"  D018 starts: {d_got14[2]['starting_tire']}")

print()
# Focus on test_095 (T=30) - D010 vs D011 at position 1
t95 = json.load(open('data/test_cases/inputs/test_095.json'))
exp95 = json.load(open('data/test_cases/expected_outputs/test_095.json'))['finishing_positions']
dt95 = get_times(t95)
print("test_095.json (T=30):")
d10 = next(d for d in dt95 if d[1] == 'D010')
d11 = next(d for d in dt95 if d[1] == 'D011')
print(f"  D010 time: {d10[0]:.6f} starts={d10[2]['starting_tire']} stops={[(x.get('lap'), x.get('to_tire')) for x in d10[2]['pit_stops']]}")
print(f"  D011 time: {d11[0]:.6f} starts={d11[2]['starting_tire']} stops={[(x.get('lap'), x.get('to_tire')) for x in d11[2]['pit_stops']]}")
print(f"  Expected winner: {exp95[0]}")
