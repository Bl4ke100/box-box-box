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
    # We will extract everything we can think of.
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    features = [0.0] * 12
    # 0..2: S, M, H laps
    # 3..5: sum of age for S, M, H
    # 6..8: max age for S, M, H
    # 9: constant time baseline
    # 10: pit lane time
    # 11: track temp
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] = max(features[6+idx], stint_len)
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        features[3+idx] += stint_len * (stint_len + 1) / 2
        features[6+idx] = max(features[6+idx], stint_len)
        
    features[9] = constant_time
    features[10] = pit_lane_time
    features[11] = temp
    
    return features

X = []
y = []

for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    feats = {d_id: get_feats(config, strats[d_id]) for d_id in finishing}
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            diff = [f1 - f2 for f1, f2 in zip(feats[d1], feats[d2])]
            # Include temp, pit lane time, total laps as context if needed, but diff is good enough?
            # Actually, temp is same for both so diff is 0. We should append TEMP to the diff vector so RF knows the temp!
            vector = diff[:10] + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(vector)
            y.append(1) # d1 beats d2
            
            # Inverse to balance dataset
            inv_vector = [-x for x in diff[:10]] + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(inv_vector)
            y.append(0)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    
    X = np.array(X)
    y = np.array(y)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X, y)
    preds = clf.predict(X)
    print(f"Training Accuracy: {accuracy_score(y, preds):.4f}")
except Exception as e:
    print("Could not run sklearn:", e)
