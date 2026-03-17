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
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    # We add sum(age^2), sum(age^3), sum(age * temp)
    features = [0.0] * 21
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        
        ages = np.arange(1, stint_len + 1)
        
        features[idx] += stint_len
        features[3+idx] += np.sum(ages)
        features[6+idx] += np.sum(ages**2)
        features[9+idx] += np.sum(ages**3)
        features[12+idx] += np.sum(ages * temp)
        features[15+idx] += np.sum(ages**2 * temp)
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        ages = np.arange(1, stint_len + 1)
        
        features[idx] += stint_len
        features[3+idx] += np.sum(ages)
        features[6+idx] += np.sum(ages**2)
        features[9+idx] += np.sum(ages**3)
        features[12+idx] += np.sum(ages * temp)
        features[15+idx] += np.sum(ages**2 * temp)
        
    features[18] = constant_time
    features[19] = pit_lane_time
    features[20] = temp
    
    return features

X = []
y = []

for race in races[:300]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    feats = {d_id: get_feats(config, strats[d_id]) for d_id in finishing}
    for i in range(len(finishing)):
        for j in range(i+1, len(finishing)):
            d1 = finishing[i]
            d2 = finishing[j]
            diff = [f1 - f2 for f1, f2 in zip(feats[d1], feats[d2])]
            vector = diff[:18] + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(vector)
            y.append(1)
            
            inv_vector = [-x for x in diff[:18]] + [config['track_temp'], config['pit_lane_time'], config['total_laps'], config['base_lap_time']]
            X.append(inv_vector)
            y.append(0)

X = np.array(X)
y = np.array(y)

try:
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    clf = MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=200, random_state=42)
    clf.fit(X_scaled, y)
    preds = clf.predict(X_scaled)
    acc = np.mean(preds == y)
    print(f"MLP Extended Features Training Accuracy: {acc:.4f}")
except Exception as e:
    print("Error:", e)
