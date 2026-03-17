import numpy as np
from scipy.optimize import minimize
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_time(race_config, strat, w):
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    var_time = 0.0
    
    def add_stint(tire, stint_len):
        nonlocal var_time
        
        idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
        base = w[idx]
        deg_base = w[3 + idx]
        temp_factor = w[6 + idx]
        
        # Exponential Temp effect: deg_rate = deg_base * exp(temp * temp_factor)
        deg_rate = deg_base * np.exp(temp * temp_factor)
        
        var_time += base * stint_len
        sum_age = stint_len * (stint_len + 1) / 2
        var_time += deg_rate * sum_age

    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        add_stint(current_tire, stint_len)
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        add_stint(current_tire, stint_len)
        
    return constant_time + var_time

eval_races = races[:200]

def loss(W):
    total_loss = 0.0
    for race in eval_races:
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        
        times = []
        for d in finishing:
            times.append(get_time(config, strats[d], W))
            
        for i in range(len(times) - 1):
            diff = times[i] - times[i+1]
            if diff > -0.01:
                total_loss += (diff + 0.01) ** 2
                
    return total_loss

# Anchor S base to 0
bounds = [
    (0, 0), (0, None), (0, None), # base S, M, H
    (0, None), (0, None), (0, None), # deg base
    (-0.5, 0.5), (-0.5, 0.5), (-0.5, 0.5) # temp_factor
]

x0 = [0.0, 1.3, 2.2, 0.1, 0.05, 0.02, 0.01, 0.01, 0.01]

res = minimize(loss, x0, method='L-BFGS-B', bounds=bounds)

print(f"Exponential Temp Loss: {res.fun:.4f}")
np.set_printoptions(suppress=True, precision=6)
print("W:", res.x)
