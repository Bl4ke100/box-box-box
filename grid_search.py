import json
import glob
import os
import itertools

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]: # load 2000 races
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    features = [0.0] * 9
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        features[idx] += stint_len
        sum_age = stint_len * (stint_len + 1) / 2
        features[3 + idx] += sum_age
        features[6 + idx] += sum_age * temp
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        sum_age = stint_len * (stint_len + 1) / 2
        features[3 + idx] += sum_age
        features[6 + idx] += sum_age * temp
        
    return features, constant_time

# Extract subset of races for fast evaluation (e.g. 50 races)
eval_races = races[:50]
eval_data = []
for r in eval_races:
    config = r['race_config']
    strats = {s['driver_id']: s for _, s in r['strategies'].items()}
    finishing = r['finishing_positions']
    feats = [get_feats(config, strats[d]) for d in finishing]
    eval_data.append(feats)

print("Precomputed eval_data.")

base_M_vals = [1.2, 1.25, 1.3]
base_H_vals = [2.0, 2.2, 2.25, 2.5]
deg_S_vals = [0.25, 0.28, 0.29, 0.3]
deg_M_vals = [0.1, 0.11, 0.12, 0.15]
deg_H_vals = [0.04, 0.045, 0.05]
temp_S_vals = [0.001, 0.0015, 0.002]
temp_M_vals = [0.0005, 0.0007, 0.00075, 0.001]
temp_H_vals = [0.0003, 0.0004, 0.0005]

def evaluate(w):
    # w = [0.0, bM, bH, dS, dM, dH, tS, tM, tH]
    correct = 0
    for feats in eval_data:
        # Check if they are perfectly sorted
        times = []
        for f, c in feats:
            t = sum(x*y for x,y in zip(w, f)) + c
            times.append(t)
        
        # If sorted ascending, then list matches sorted list
        if all(times[i] < times[i+1] for i in range(len(times)-1)):
            correct += 1
    return correct

best = 0
best_w = None

total_combos = (len(base_M_vals) * len(base_H_vals) * len(deg_S_vals) * len(deg_M_vals) * 
                len(deg_H_vals) * len(temp_S_vals) * len(temp_M_vals) * len(temp_H_vals))

print(f"Total combinations: {total_combos}")

for bM in base_M_vals:
    for bH in base_H_vals:
        for dS in deg_S_vals:
            for dM in deg_M_vals:
                for dH in deg_H_vals:
                    for tS in temp_S_vals:
                        for tM in temp_M_vals:
                            for tH in temp_H_vals:
                                w = [0.0, bM, bH, dS, dM, dH, tS, tM, tH]
                                score = evaluate(w)
                                if score > best:
                                    best = score
                                    best_w = w
                                    print(f"New best: {best}/50 -> {w}")

print(f"Best score: {best}/50")
print(f"Best W: {best_w}")

