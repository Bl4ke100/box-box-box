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

def get_feats(race_config, strat):
    # Just the 9 basic features + pit lane + diff C
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    features = [0.0] * 9
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] += stint_len * (stint_len + 1) / 2 * temp
        
    return features, constant_time


X = []
y = []

# Exclude identical pairs
for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    feats = {d_id: get_feats(config, strats[d_id]) for d_id in finishing}
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            
            f1, c1 = feats[d1]
            f2, c2 = feats[d2]
            
            diff_f = [x1 - x2 for x1, x2 in zip(f1, f2)]
            diff_C = c1 - c2
            
            # Non-identical only
            if not (all(abs(v) < 0.001 for v in diff_f) and abs(diff_C) < 0.001):
                vec = diff_f + [diff_C]
                X.append(vec)
                y.append(1)  # D1 beats D2
                
                inv_vec = [-v for v in diff_f] + [-diff_C]
                X.append(inv_vec)
                y.append(0)  # D2 loses to D1

X = np.array(X)
y = np.array(y)

print(f"Total non-tied samples: {len(X)}")

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier

clf = ExtraTreesClassifier(n_estimators=200, max_depth=20, random_state=42)
clf.fit(X, y)
preds = clf.predict(X)
acc = np.mean(preds == y)
print(f"ExtraTrees Extracted Features Accuracy: {acc:.4f}")

mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
mlp.fit(X, y)
preds_mlp = mlp.predict(X)
acc_mlp = np.mean(preds_mlp == y)
print(f"MLP Extracted Features Accuracy: {acc_mlp:.4f}")
