import os
import json

def get_times(test_file):
    with open(test_file, 'r') as f:
        t = json.load(f)
        
    config = t['race_config']
    strats = t['strategies']
    
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25:
        t_mult = 0.8
    elif temp <= 34:
        t_mult = 1.0
    else:
        t_mult = 1.3
        
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
            
        driver_times.append((time, d_id))
        
    # Python stable sort
    driver_times.sort(key=lambda x: x[0])
    return driver_times

t2 = get_times("data/test_cases/inputs/test_002.json")
with open("data/test_cases/expected_outputs/test_002.json", 'r') as f:
    e2 = json.load(f)['finishing_positions']

print("EXPECTED:")
print(e2)
print("\nPREDICTED TIMES (All 20):")
for time, d_id in t2:
    print(f"{d_id}: {time:.6f}")
