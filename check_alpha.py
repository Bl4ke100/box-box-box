import os
import glob
import json

def get_times(t):
    config = t['race_config']
    strats = t['strategies']
    
    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']
    
    if temp < 25: t_mult = 0.8
    elif temp <= 34: t_mult = 1.0
    else: t_mult = 1.3
        
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
        
    driver_times.sort(key=lambda x: (round(x[0], 5), x[1])) # Alpha sorting ASCENDING
    return driver_times

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    all_reverse_alpha = True
    fail_count = 0
    
    for test_file in test_files:
        name = os.path.basename(test_file)
        expected_file = os.path.join(expected_dir, name)
        if not os.path.exists(expected_file): continue
            
        with open(test_file, 'r') as f: t = json.load(f)
        with open(expected_file, 'r') as f: e = json.load(f)['finishing_positions']
        
        d_times = get_times(t)
        predicted = [dt[1] for dt in d_times]
        
        if e != predicted:
            fail_count += 1
            # Check if sorting REVERSE alphabetical would fix the swap
            d_times_rev = sorted(d_times, key=lambda x: (round(x[0], 5), x[1]), reverse=False)
            # Wait, natively it was alphabetical. Let's sort manually in python:
            # Ascending time, but descending string
            d_times_custom = sorted(d_times, key=lambda x: (round(x[0], 5), -int(x[1].replace('D',''))))
            pred_custom = [dt[1] for dt in d_times_custom]
            
            if e != pred_custom:
                all_reverse_alpha = False
                print(f"{name} is not entirely reverse alphabetical ties.")
                print(f"Expected: {e}")
                print(f"Custom:   {pred_custom}")
                break
                
    print(f"Total Fails Before Reverse-Alpha: {fail_count}")
    print(f"Is rule strictly Reverse-Alphabetical ID? {all_reverse_alpha}")

if __name__ == '__main__':
    main()
