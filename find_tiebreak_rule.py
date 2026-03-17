"""
Mine historical races to find identical-time pairs and determine tiebreaking rule.
"""
import json, glob, os, numpy as np

def get_params(temp):
    if temp < 25: tmult = 0.8
    elif temp <= 34: tmult = 1.0
    else: tmult = 1.3
    base = {'SOFT': 0.0198, 'MEDIUM': 0.01, 'HARD': 0.005}
    return {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}, {k: v*tmult for k, v in base.items()}

def compute_time(config, strat, c_offset, deg_rate, th={'SOFT':10,'MEDIUM':20,'HARD':30}):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    total_laps = config['total_laps']
    time = plt * len(strat['pit_stops'])
    current_lap = 1
    current_tire = strat['starting_tire']
    stints = []
    for stop in strat['pit_stops']:
        stints.append((current_tire, stop['lap'] - current_lap + 1))
        current_lap = stop['lap'] + 1
        current_tire = stop['to_tire']
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
    for tire, slen in stints:
        time += (blt + c_offset[tire]) * slen
        K = max(0, slen - th[tire])
        time += (K*(K+1)/2) * blt * deg_rate[tire]
    last_tire, last_slen = stints[-1]
    last_deg = max(0, last_slen - th[last_tire])
    last_lap = blt + c_offset[last_tire] + last_deg * blt * deg_rate[last_tire]
    return time, stints, last_lap

data_dir = r"data/historical_races"
files = sorted(glob.glob(os.path.join(data_dir, "*.json")))

grid_wins = 0
num_wins = 0
total_ties = 0
exception_cases_lower_first = 0  # winner had higher grid but SLOWER first stint
exception_cases_faster_first = 0  # winner had higher grid but FASTER first stint

for f in files[:5]:
    races = json.load(open(f))
    for race in races:
        config = race['race_config']
        strats = race['strategies']
        strat_map = {s['driver_id']: s for s in strats.values()}
        pos_map = {s['driver_id']: int(pos.replace('pos', '')) for pos, s in strats.items()}
        e = race['finishing_positions']
        
        c_offset, deg_rate = get_params(config['track_temp'])
        
        times = {}
        stints_map = {}
        last_laps = {}
        for d_id, s in strat_map.items():
            times[d_id], stints_map[d_id], last_laps[d_id] = compute_time(config, s, c_offset, deg_rate)
        
        COMP_ORDER = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}
        
        for i in range(len(e) - 1):
            w, l = e[i], e[i+1]
            if abs(times[w] - times[l]) < 1e-8:
                total_ties += 1
                gw, gl = pos_map[w], pos_map[l]
                if gw > gl:  # winner has HIGHER grid number (worse grid)
                    # Check if winner had faster first stint compound
                    fw = COMP_ORDER[stints_map[w][0][0]]
                    fl = COMP_ORDER[stints_map[l][0][0]]
                    if fw < fl:  # winner started on faster compound
                        exception_cases_faster_first += 1
                    else:
                        exception_cases_lower_first += 1

print(f"Total identical-time pairs in historical data: {total_ties}")
print(f"Exceptions (higher grid won): {exception_cases_faster_first + exception_cases_lower_first}")
print(f"  - Of those, winner had faster starting compound: {exception_cases_faster_first}")
print(f"  - Of those, winner had slower starting compound: {exception_cases_lower_first}")
