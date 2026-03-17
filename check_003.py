import json
import final_test_runner as ftr

test_case = json.load(open('data/test_cases/inputs/test_003.json'))
d_times = []

config = test_case['race_config']
strats = test_case['strategies']
blt, plt, temp, total_laps = config['base_lap_time'], config['pit_lane_time'], config['track_temp'], config['total_laps']

t_mult = 0.8 if temp < 25 else 1.0 if temp <= 34 else 1.3
c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}
deg_rate = {'SOFT': 0.02, 'MEDIUM': 0.01, 'HARD': 0.005}
th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}

for pos, s in strats.items():
    if s['driver_id'] in ['D013', 'D011']:
        time = plt * len(s['pit_stops'])
        current_lap, current_tire = 1, s['starting_tire']
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
            time += (K * (K + 1)) / 2 * blt * deg_rate[tire] * t_mult
            
        last_tire, last_slen = stints[-1]
        last_deg = max(0, last_slen - th[last_tire])
        last_lap_time = blt + c_offset[last_tire] + last_deg * blt * deg_rate[last_tire] * t_mult
        
        print(f"Driver {s['driver_id']}: Time={time:.6f}, LastLap={last_lap_time:.6f}, Grid={pos}, Strats={s['starting_tire']} -> {s['pit_stops']}")
