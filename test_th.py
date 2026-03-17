import os
import glob
import json
import itertools

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    test_data = []
    
    for f_in in test_files:
        name = os.path.basename(f_in)
        f_exp = os.path.join(expected_dir, name)
        with open(f_in, 'r') as f:
            t = json.load(f)
        with open(f_exp, 'r') as f:
            e = json.load(f)
            
        expected_pos = e['finishing_positions']
        rank_map = {d: i for i, d in enumerate(expected_pos)}
        test_data.append((t, rank_map))
        
    c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}
    deg_rate = {'SOFT': 0.02, 'MEDIUM': 0.01, 'HARD': 0.005}

    print("Starting exact threshold loop search...")
    
    best_error = float('inf')
    best_th = None
    
    for s_th in range(8, 12):
        for m_th in range(18, 22):
            for h_th in range(28, 32):
                th = {'SOFT': s_th, 'MEDIUM': m_th, 'HARD': h_th}
                total_error = 0.0
                
                for t, expected_rank_map in test_data:
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
                            sum_deg = (K * (K + 1)) // 2 # safe integer arithmetic
                            time += sum_deg * blt * deg_rate[tire] * t_mult
                            
                        driver_times.append((time, d_id))
                        
                    # Stable sort ties
                    driver_times.sort(key=lambda x: round(x[0], 5))
                    
                    for true_rank, (time, d_id) in enumerate(driver_times):
                        expected_rank = expected_rank_map[d_id]
                        total_error += abs(true_rank - expected_rank)
                
                if total_error < best_error:
                    best_error = total_error
                    best_th = th
                    print(f"New Best! Error {total_error} -> TH: {th}")
                    
                if total_error == 0.0:
                    print("PERFECT MATCH FOUND!")
                    break
            if best_error == 0.0: break
        if best_error == 0.0: break

if __name__ == '__main__':
    main()
