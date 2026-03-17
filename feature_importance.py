import json
import glob
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
    # Let's add LOTS of features so the Random Forest can tell us what matters!
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    features = [0.0] * 15
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        stints.append((current_tire, stint_len))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        stints.append((current_tire, stint_len))
        
    for tire, slen in stints:
        idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
        features[idx] += slen
        sum_age = slen * (slen + 1) / 2
        features[3+idx] += sum_age
        features[6+idx] += sum_age * temp
        features[9+idx] = max(features[9+idx], slen)
        sum_sq = slen * (slen + 1) * (2*slen + 1) / 6
        features[12+idx] += sum_sq
        
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
            
            if not (all(abs(v) < 0.001 for v in diff_f) and abs(diff_C) < 0.001):
                vec = diff_f + [diff_C]
                X.append(vec)
                y.append(1)  # D1 beats D2
                
                inv_vec = [-v for v in diff_f] + [-diff_C]
                X.append(inv_vec)
                y.append(0)

X = np.array(X)
y = np.array(y)

clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
clf.fit(X, y)
print(f"Accuracy: {np.mean(clf.predict(X) == y):.4f}")

feature_names = [
    "S_laps", "M_laps", "H_laps",
    "S_sum_age", "M_sum_age", "H_sum_age",
    "S_sum_age_temp", "M_sum_age_temp", "H_sum_age_temp",
    "S_max_stint", "M_max_stint", "H_max_stint",
    "S_sum_sq_age", "M_sum_sq_age", "H_sum_sq_age",
    "Diff_Constant"
]

importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]

print("Feature Importances:")
for f in range(len(feature_names)):
    print(f"{feature_names[indices[f]]}: {importances[indices[f]]:.4f}")

