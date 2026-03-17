"""
For each failing test, check exactly what times our model computes vs what's correct.
This helps diagnose if the issue is compound offset, degradation, or something else.
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
    return time

# Look at all failing tests and analyze what C_S, C_H values would be needed to fix each swap
failing = [
    ('test_006.json', 'D003', 'D018', 13, 14),  # 14th vs 15th
    ('test_011.json', 'D004', 'D007', 4, 5),
    ('test_014.json', 'D002', 'D017', 2, 3),
    ('test_040.json', 'D014', 'D012', 0, 1),
    ('test_095.json', 'D010', 'D011', 0, 1),
]

print("Analyzing what parameter changes would fix each swap:\n")

for test_name, winner, loser, w_pos, l_pos in failing:
    t = json.load(open(f'data/test_cases/inputs/{test_name}'))
    config = t['race_config']
    temp = config['track_temp']
    strats = {s['driver_id']: s for s in t['strategies'].values()}
    
    c_offset, deg_rate = get_params(temp)
    
    t1 = compute_time(config, strats[winner], c_offset, deg_rate)
    t2 = compute_time(config, strats[loser], c_offset, deg_rate)
    
    print(f"{test_name} (T={temp}): expects {winner} before {loser}")
    print(f"  Our model: {winner}={t1:.4f}, {loser}={t2:.4f}, diff={t1-t2:.4f}")
    
    # Figure out the stints for each
    total_laps = config['total_laps']
    def get_stints(d_id):
        s = strats[d_id]
        current_lap, current_tire = 1, s['starting_tire']
        stints = []
        for stop in s['pit_stops']:
            stints.append((current_tire, stop['lap'] - current_lap + 1))
            current_lap = stop['lap'] + 1
            current_tire = stop['to_tire']
        if current_lap <= total_laps:
            stints.append((current_tire, total_laps - current_lap + 1))
        return stints
    
    sw = get_stints(winner)
    sl = get_stints(loser)
    print(f"  {winner} stints: {sw}")
    print(f"  {loser} stints: {sl}")
    
    # Compute how much C_S would need to change to fix the swap
    # t1_cs = sum(slen for t,slen in sw if t=='SOFT') * delta_cs
    # t2_cs = sum(slen for t,slen in sl if t=='SOFT') * delta_cs
    # Need (t1 + delta_cs * soft1 + delta_ch * hard1) < (t2 + delta_cs * soft2 + delta_ch * hard2)
    soft1 = sum(slen for t,slen in sw if t=='SOFT')
    soft2 = sum(slen for t,slen in sl if t=='SOFT')
    hard1 = sum(slen for t,slen in sw if t=='HARD')
    hard2 = sum(slen for t,slen in sl if t=='HARD')
    print(f"  Soft laps: {winner}={soft1}, {loser}={soft2}; Hard laps: {winner}={hard1}, {loser}={hard2}")
    print()
