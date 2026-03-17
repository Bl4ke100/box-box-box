import os
import glob
import json

def manual_sim(file_path):
    with open(file_path, 'r') as f:
        test_case = json.load(f)
        
    config = test_case['race_config']
    strats = test_case['strategies']
    
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    with open('temp_map.json') as f:
        t_map = json.load(f)
    
    t_str = str(temp)
    if t_str not in t_map:
        # Fallback to closest
        t_closest = min(t_map.keys(), key=lambda k: abs(int(k) - temp))
        params = t_map[t_closest]
    else:
        params = t_map[t_str]
        
    c_offset = {'SOFT': params[0], 'MEDIUM': 0.0, 'HARD': params[1]}
    deg_rate_c = {'SOFT': params[2], 'MEDIUM': params[3], 'HARD': params[4]}
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}
    
    COMPOUND_SPEED = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}  # 0=fastest
    
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
            
        first_compound_speed = COMPOUND_SPEED[stints[0][0]]
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((time, first_compound_speed, grid_pos, d_id))
        
    driver_times.sort(key=lambda x: (round(x[0], 4), x[1], x[2]))
    return [d_id for time, fcs, grid, d_id in driver_times]

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    passed = 0
    total = len(test_files)
    
    failed_details = []
    
    for test_file in test_files:
        test_name = os.path.basename(test_file)
        expected_file = os.path.join(expected_dir, test_name)
        
        predicted = manual_sim(test_file)
        
        if os.path.exists(expected_file):
            with open(expected_file, 'r') as f:
                expected = json.load(f)['finishing_positions']
                
            if predicted == expected:
                passed += 1
            else:
                failed_details.append((test_name, expected, predicted))
                
    print(f"RESULTS: {passed} / {total} Passed ({passed/total*100:.1f}%)")
    if failed_details:
        print("Failed tests:", [f[0] for f in failed_details])
        print(f"\nExample Failure ({failed_details[0][0]}):")
        print("Expected:", failed_details[0][1])
        print("Got:     ", failed_details[0][2])

if __name__ == '__main__':
    main()
