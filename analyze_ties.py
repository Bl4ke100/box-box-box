"""
All remaining failures are EXACT TIES (diff=0.0000).
Analyze the tied drivers to find the correct tie-breaking rule.
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
    return time, stints

failing_tests = [
    'test_006.json', 'test_011.json', 'test_013.json', 'test_014.json',
    'test_018.json', 'test_022.json', 'test_028.json', 'test_029.json',
    'test_031.json', 'test_032.json', 'test_034.json', 'test_035.json',
    'test_040.json', 'test_041.json', 'test_043.json', 'test_045.json',
    'test_046.json', 'test_050.json', 'test_054.json', 'test_055.json',
    'test_057.json', 'test_058.json', 'test_061.json', 'test_062.json',
    'test_066.json', 'test_070.json', 'test_071.json', 'test_073.json',
    'test_079.json', 'test_082.json', 'test_085.json', 'test_090.json',
    'test_093.json', 'test_094.json', 'test_095.json', 'test_098.json',
]

tie_pairs = []  # (winner_id, loser_id, grid_w, grid_l, stints_w, stints_l, blt, temp, total_laps)

for test_name in failing_tests:
    t = json.load(open(f'data/test_cases/inputs/{test_name}'))
    e = json.load(open(f'data/test_cases/expected_outputs/{test_name}'))['finishing_positions']
    config = t['race_config']
    temp = config['track_temp']
    strats_by_id = {s['driver_id']: s for s in t['strategies'].values()}
    strats_by_pos = t['strategies']
    pos_to_id = {pos: s['driver_id'] for pos, s in strats_by_pos.items()}
    id_to_pos = {s['driver_id']: pos for pos, s in strats_by_pos.items()}
    
    c_offset, deg_rate = get_params(temp)
    
    # Find all pairs of drivers with exactly equal times
    times = {}
    stints_map = {}
    for d_id, s in strats_by_id.items():
        tt, stints = compute_time(config, s, c_offset, deg_rate)
        times[d_id] = tt
        stints_map[d_id] = stints
    
    # Find adjacent pairs in expected that have same time
    for i in range(len(e) - 1):
        w, l = e[i], e[i+1]
        if abs(times[w] - times[l]) < 1e-8:
            grid_w = int(id_to_pos[w].replace('pos', ''))
            grid_l = int(id_to_pos[l].replace('pos', ''))
            tie_pairs.append({
                'test': test_name, 
                'temp': temp,
                'winner': w, 'loser': l,
                'grid_w': grid_w, 'grid_l': grid_l,
                'num_w': int(w.replace('D','')), 'num_l': int(l.replace('D','')),
                'stints_w': stints_map[w], 'stints_l': stints_map[l],
                'blt': config['base_lap_time'],
                'total_laps': config['total_laps'],
                'pits_w': len(strats_by_id[w]['pit_stops']),
                'pits_l': len(strats_by_id[l]['pit_stops']),
            })

print(f"\nTotal tie pairs: {len(tie_pairs)}")
print("\nSample tie analysis:")
# Analysis: does winner always have lower grid position?
grid_correct = sum(1 for p in tie_pairs if p['grid_w'] < p['grid_l'])
grid_wrong = sum(1 for p in tie_pairs if p['grid_w'] > p['grid_l'])
grid_equal = sum(1 for p in tie_pairs if p['grid_w'] == p['grid_l'])
print(f"Grid position: winner has lower grid {grid_correct}/{len(tie_pairs)} times, higher {grid_wrong}, equal {grid_equal}")

num_correct = sum(1 for p in tie_pairs if p['num_w'] < p['num_l'])
num_wrong = sum(1 for p in tie_pairs if p['num_w'] > p['num_l'])
print(f"Driver numeric ID: winner has lower num {num_correct}/{len(tie_pairs)} times, higher {num_wrong}")

# Does winner have fewer pit stops?
pits_fewer = sum(1 for p in tie_pairs if p['pits_w'] < p['pits_l'])
pits_more = sum(1 for p in tie_pairs if p['pits_w'] > p['pits_l'])
pits_equal = sum(1 for p in tie_pairs if p['pits_w'] == p['pits_l'])
print(f"Pit stops: winner has fewer pits {pits_fewer}/{len(tie_pairs)} times, more {pits_more}, equal {pits_equal}")

# Print the grid-wrong cases to understand pattern
print("\nCases where lower grid position does NOT win:")
for p in tie_pairs:
    if p['grid_w'] > p['grid_l']:
        print(f"  {p['test']}: {p['winner']}(grid={p['grid_w']}) beats {p['loser']}(grid={p['grid_l']})")
        print(f"    Winner stints: {p['stints_w']}")
        print(f"    Loser  stints: {p['stints_l']}")
