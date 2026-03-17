import numpy as np
from scipy.optimize import minimize
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_time(race_config, strat, w):
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    # w contains: 
    # base_M (0), base_H (1)
    # deg_S (2), deg_M (3), deg_H (4)
    # temp_S (5), temp_M (6), temp_H (7)
    # exponent (8)
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    var_time = 0.0
    
    def add_stint(tire, stint_len):
        nonlocal var_time
        
        if tire == 'SOFT':
            base = 0.0
            deg = w[2]
            t = w[5]
        elif tire == 'MEDIUM':
            base = w[0]
            deg = w[3]
            t = w[6]
        else:
            base = w[1]
            deg = w[4]
            t = w[7]
            
        exponent = w[8]
        
        var_time += base * stint_len
        
        ages = np.arange(1, stint_len + 1)
        # Try exponential-like polynomials
        total_deg = np.sum((deg + t * temp) * (ages ** exponent))
        var_time += total_deg

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

eval_races = races[:100]

def loss(W):
    total_loss = 0.0
    for race in eval_races:
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        
        times = []
        for d in finishing:
            times.append(get_time(config, strats[d], W))
            
        # We want times to be strictly ascending
        for i in range(len(times) - 1):
            diff = times[i] - times[i+1] # should be < 0
            if diff > -0.01:
                total_loss += (diff + 0.01) ** 2
                
    return total_loss

bounds = [
    (0, None), (0, None), # base M, H
    (0, None), (0, None), (0, None), # deg
    (0, None), (0, None), (0, None), # temp
    (1.0, 5.0) # exponent
]

# Initial guess slightly off linear
x0 = [1.3, 2.2, 0.3, 0.1, 0.05, 0.001, 0.0005, 0.0002, 1.5]

res = minimize(loss, x0, method='L-BFGS-B', bounds=bounds)

print(f"Loss: {res.fun:.4f}")
np.set_printoptions(suppress=True, precision=6)
print("W:", res.x)
