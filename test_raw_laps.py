import json
import glob
import os
import numpy as np

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_raw_laps(race_config, strat):
    # Returns an array length max_laps (e.g. 70) of (compound, age)
    total_laps = race_config['total_laps']
    
    laps = []
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        for age in range(1, stint_len + 1):
            laps.append((idx, age))
            
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        for age in range(1, stint_len + 1):
            laps.append((idx, age))
            
    # pad to 70 laps
    while len(laps) < 70:
        laps.append((-1, 0)) # No tire, age 0
        
    return laps

X = []
y = []

# Use only non-identical exact strategy pairs!
for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    feats = {d_id: get_raw_laps(config, strats[d_id]) for d_id in finishing}
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            
            laps1 = feats[d1]
            laps2 = feats[d2]
            
            # Flatten
            flat1 = []
            for tire, age in laps1:
                flat1.extend([tire, age])
                
            flat2 = []
            for tire, age in laps2:
                flat2.extend([tire, age])
                
            # diff? ML might handle diff better if it's just raw concatenated
            # Actually, just concatenate flat1, flat2, config features
            vector = flat1 + flat2 + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(vector)
            y.append(1)
            
            inv_vector = flat2 + flat1 + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(inv_vector)
            y.append(0)

X = np.array(X)
y = np.array(y)

try:
    from sklearn.ensemble import ExtraTreesClassifier
    from sklearn.model_selection import train_test_split
    
    clf = ExtraTreesClassifier(n_estimators=100, max_depth=15, random_state=42)
    clf.fit(X, y)
    preds = clf.predict(X)
    acc = np.mean(preds == y)
    print(f"ExtraTrees Raw Laps Accuracy: {acc:.4f}")
except Exception as e:
    print("Error:", e)

