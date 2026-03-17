import json
import glob
import os
import numpy as np
import pickle
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
# Load 15 files -> ~15,000 races
print("Loading races...")
for f in files[:15]:
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

X_train = []
y_train = []

train_races = races[:2500]
test_races = races[2500:3000]

print("Extracting training sequences...")
for race in train_races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    vecs = {d: get_stints_vector(config, strats[d]) for d in finishing}
    
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            
            v1 = vecs[d1]
            v2 = vecs[d2]
            
            if v1 == v2:
                continue
                
            base_feats = [config['track_temp'], config['base_lap_time'], config['pit_lane_time'], config['total_laps']]
            
            X_train.append(v1 + v2 + base_feats)
            y_train.append(1)
            
            X_train.append(v2 + v1 + base_feats)
            y_train.append(0)

X_train = np.array(X_train)
y_train = np.array(y_train)

print(f"Training on {len(X_train)} samples...")
clf = ExtraTreesClassifier(n_estimators=300, max_depth=30, min_samples_split=2, n_jobs=-1, random_state=42)
clf.fit(X_train, y_train)

import joblib
joblib.dump(clf, "ai_model.pkl")

X_test = []
y_test = []
print("Evaluating on absolute ranking metrics for Test races...")

# For metric strictly calculating exact 1-20 ranking
perfect_races = 0

for race in test_races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    drivers = list(strats.keys())
    # Sort them alphabetically first as an initial tie breaker baseline
    drivers.sort()
    
    vecs = {d: get_stints_vector(config, strats[d]) for d in drivers}
    
    def compare_drivers(d1, d2):
        v1 = vecs[d1]
        v2 = vecs[d2]
        
        if v1 == v2:
            return 0 # identical structurally
        
        base_feats = [config['track_temp'], config['base_lap_time'], config['pit_lane_time'], config['total_laps']]
        
        # We need D1 vs D2 score
        pred = clf.predict([v1 + v2 + base_feats])[0]
        
        # pred == 1 means D1 wins
        if pred == 1:
            return -1 # D1 less time than D2
        else:
            return 1

    import functools
    pred_order = sorted(drivers, key=functools.cmp_to_key(compare_drivers))
    
    if pred_order == finishing:
        perfect_races += 1
        
print(f"PERFECT Entire-Race Predictions: {perfect_races} / {len(test_races)} ({(perfect_races/len(test_races))*100:.2f}%)")

