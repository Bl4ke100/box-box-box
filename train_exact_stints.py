import json
import glob
import os
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

c_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_stints_vector(race_config, strat):
    # Fixed size vector for up to 6 stints
    # For each stint: [compound, length]
    # Rest filled with [-1, 0]
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
        
    # Pad to 6 stints (12 values)
    while len(vec) < 12:
        vec.extend([-1, 0])
        
    return vec

X = []
y = []

print("Extracting perfectly ordered sequences...")
for race in races[:600]:
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
            
            # Simple check for exactly identically structured strategies
            if v1 == v2:
                continue
                
            # Inputs: [V1, V2, Temp, Base_Lap, Pit_Time, Total_Laps]
            base_feats = [config['track_temp'], config['base_lap_time'], config['pit_lane_time'], config['total_laps']]
            
            X.append(v1 + v2 + base_feats)
            y.append(1)
            
            X.append(v2 + v1 + base_feats)
            y.append(0)

X = np.array(X)
y = np.array(y)

print(f"Training on {len(X)} samples...")
clf = ExtraTreesClassifier(n_estimators=100, max_depth=20, n_jobs=-1, random_state=42)
clf.fit(X, y)

preds = clf.predict(X)
acc = accuracy_score(y, preds)
print(f"ExtraTrees Sequence Accuracy: {acc:.4f}")

