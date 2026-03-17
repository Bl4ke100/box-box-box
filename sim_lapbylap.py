"""
Test if a lap-by-lap simulation creates floating-point differences that naturally 
break ties without any explicit tie-breaking rule.

If the base simulator runs lap-by-lap (adding each lap's time iteratively),
floating-point arithmetic creates tiny differences that serve as the inherent tie-breaker.
"""
import json, glob, os

def sim_lapbylap(config, strats):
    """Simulate lap-by-lap, returning sorted finishing positions."""
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25: tmult = 0.8
    elif temp <= 34: tmult = 1.0
    else: tmult = 1.3
    
    c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}
    deg_rate = {'SOFT': 0.0198 * tmult, 'MEDIUM': 0.01 * tmult, 'HARD': 0.005 * tmult}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    driver_times = []
    
    for pos, s in strats.items():
        d_id = s['driver_id']
        
        # Build lap sequence
        current_lap = 1
        current_tire = s['starting_tire']
        current_age = 1  # tire age starts at 1
        stops = s['pit_stops']
        pit_laps = {stop['lap']: stop['to_tire'] for stop in stops}
        
        total_time = 0.0
        
        for lap in range(1, total_laps + 1):
            # Add lap time for this lap
            deg = max(0, current_age - th[current_tire])
            lap_time = blt + c_offset[current_tire] + deg * blt * deg_rate[current_tire]
            total_time += lap_time
            
            # Check if pit stop happens after this lap
            if lap in pit_laps:
                total_time += plt  # pit stop time
                current_tire = pit_laps[lap]
                current_age = 1
            else:
                current_age += 1
        
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((total_time, grid_pos, d_id))
    
    # Sort purely by time, then grid position as tiebreak
    driver_times.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in driver_times]

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    passed = 0
    failed_tests = []
    
    for f in test_files:
        name = os.path.basename(f)
        t = json.load(open(f))
        pred = sim_lapbylap(t['race_config'], t['strategies'])
        exp = json.load(open(os.path.join(expected_dir, name)))['finishing_positions']
        if pred == exp:
            passed += 1
        else:
            diffs = [(i, exp[i], pred[i]) for i in range(20) if exp[i] != pred[i]]
            failed_tests.append((name, diffs[:3]))
    
    print(f"RESULTS: {passed}/100 ({passed}%)")
    if failed_tests:
        print(f"\nALL {len(failed_tests)} failures:")
        for name, diffs in failed_tests:
            t_data = json.load(open(os.path.join(test_cases_dir, name)))
            temp = t_data['race_config']['track_temp']
            print(f"  {name} (T={temp}): {diffs}")

if __name__ == '__main__':
    main()
