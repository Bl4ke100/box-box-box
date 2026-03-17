import json
import glob
import os
import numpy as np
import joblib

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

c_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_stints_vector(race_config, strat):
    vec = []
    total_laps = race_config['total_laps']
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stints.append((current_tire, pit_lap - current_lap + 1))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
        
    for tire, slen in stints:
        vec.extend([c_map[tire], slen])
        
    while len(vec) < 12:
        vec.extend([-1, 0])
        
    return vec

test_races = races[2500:3500] # Use next 1000

print("Loading AI Model...")
clf = joblib.load("ai_model.pkl")
print("Model loaded. Evaluating...")

perfect_races = 0

for race in test_races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    drivers = list(strats.keys())
    # Base alphabetical sort
    drivers.sort()
    
    vecs = {d: get_stints_vector(config, strats[d]) for d in drivers}
    base_feats = [config['track_temp'], config['base_lap_time'], config['pit_lane_time'], config['total_laps']]
    
    # We want to properly SORT the 20 drivers.
    # We can just compute a "win count" for each driver to sort them!
    # If D1 beats D2, D1's win count +1.
    # The driver with 19 wins is 1st place. The one with 18 wins is 2nd...
    # This is a mathematically guaranteed perfect strict topological sort array 
    # IF the pairwise predictions are internally consistent!
    
    batch_X = []
    pairs = []
    
    for i in range(len(drivers)):
        for j in range(i+1, len(drivers)):
            d1 = drivers[i]
            d2 = drivers[j]
            v1 = vecs[d1]
            v2 = vecs[d2]
            
            # Predict D1 vs D2
            batch_X.append(v1 + v2 + base_feats)
            pairs.append((d1, d2))
            
    if len(batch_X) == 0:
        continue
        
    batch_X = np.array(batch_X)
    preds = clf.predict(batch_X)
    
    wins = {d: 0 for d in drivers}
    
    for idx, (d1, d2) in enumerate(pairs):
        # tie breakers handled automatically if we don't increment win when tied?
        # But predict only outputs 0 or 1.
        if preds[idx] == 1:
            wins[d1] += 1
        else:
            wins[d2] += 1
            
    # Sort drivers by points DESCENDING, then alphabetically
    def sort_key(d):
        return (-wins[d], d)
        
    pred_order = sorted(drivers, key=sort_key)
    
    if pred_order == finishing:
        perfect_races += 1

print(f"FAST EVAL: {perfect_races} / {len(test_races)} ({(perfect_races/len(test_races))*100:.2f}%)")

