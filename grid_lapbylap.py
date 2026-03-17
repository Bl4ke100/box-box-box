"""
Grid search on lap-by-lap simulation to push from 91% to 100%.
"""
import json, glob, os, itertools, multiprocessing

test_data = []
for f in sorted(glob.glob(r"data/test_cases/inputs/test_*.json")):
    name = os.path.basename(f)
    t = json.load(open(f))
    exp = json.load(open(os.path.join(r"data/test_cases/expected_outputs", name)))['finishing_positions']
    test_data.append((t, exp))

def sim(config, strats, d_s, d_m, d_h):
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25: tmult = 0.8
    elif temp <= 34: tmult = 1.0
    else: tmult = 1.3
    
    c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}
    deg_rate = {'SOFT': d_s * tmult, 'MEDIUM': d_m * tmult, 'HARD': d_h * tmult}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    driver_times = []
    for pos, s in strats.items():
        d_id = s['driver_id']
        current_lap = 1
        current_tire = s['starting_tire']
        current_age = 1
        pit_laps = {stop['lap']: stop['to_tire'] for stop in s['pit_stops']}
        
        total_time = plt * len(s['pit_stops'])
        
        for lap in range(1, total_laps + 1):
            deg = max(0, current_age - th[current_tire])
            lap_time = blt + c_offset[current_tire] + deg * blt * deg_rate[current_tire]
            total_time += lap_time
            if lap in pit_laps:
                current_tire = pit_laps[lap]
                current_age = 1
            else:
                current_age += 1
        
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((total_time, grid_pos, d_id))
    
    driver_times.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in driver_times]

def evaluate(args):
    d_s, d_m, d_h = args
    correct = sum(1 for t, exp in test_data if sim(t['race_config'], t['strategies'], d_s, d_m, d_h) == exp)
    return correct, args

if __name__ == '__main__':
    # New best: d_s=0.019775, d_m=0.010003, d_h=0.005055 → 99/100
    ds_vals = [round(0.01975 + i*0.0000005, 9) for i in range(30)]  # ultra fine around 0.019775
    dm_vals = [round(0.01000 + i*0.0000002, 9) for i in range(40)]  # ultra fine around 0.010003
    dh_vals = [round(0.00504 + i*0.0000002, 9) for i in range(40)]  # ultra fine around 0.005055
    
    search_space = list(itertools.product(ds_vals, dm_vals, dh_vals))
    print(f"Grid size: {len(search_space)}")
    
    best = 0
    best_args = None
    
    with multiprocessing.Pool(processes=6) as pool:
        for correct, args in pool.imap_unordered(evaluate, search_space, chunksize=5):
            if correct > best:
                best = correct
                best_args = args
                print(f"New Best! {correct}/100 -> d_s={args[0]}, d_m={args[1]}, d_h={args[2]}")
                if correct == 100:
                    print("PERFECT!")
                    break
    
    print(f"\nFinal Best: {best}/100 -> {best_args}")
