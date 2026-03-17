import json
import os
import glob
import random

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:  # 2000 races
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
    # Features: [S_laps, M_laps, H_laps, S_age, M_age, H_age, S_temp, M_temp, H_temp]
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    
    features = [0.0] * 9
    
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
        
    return features

X = []
for race in races:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1 = get_feats(config, strats[d1])
        f2 = get_feats(config, strats[d2])
        
        # We want Time(d1) < Time(d2)
        # So f1*W < f2*W  =>  (f2 - f1)*W > 0
        diff = [x2 - x1 for x1, x2 in zip(f1, f2)]
        
        # If diff is entirely 0, they had identical features, skip
        if any(abs(v) > 0.0001 for v in diff):
            X.append(diff)

print(f"Total inequalities: {len(X)}")

W = [0.5] * 9
W[0] = 0.0 # base_S offset is 0 by definition (reference tire)

learning_rate = 0.001
epochs = 200
for epoch in range(epochs):
    violations = 0
    random.shuffle(X)
    for x in X:
        dot = sum(w * v for w, v in zip(W, x))
        # strictly greater than 0, add a small margin
        if dot <= 0.001:
            violations += 1
            for i in range(1, 9): # update all except W[0]
                W[i] += learning_rate * x[i]
            # Clip to non-negative
            for i in range(1, 9):
                if W[i] < 0: W[i] = 0.0
                
    if epoch % 10 == 0:
        print(f"Epoch {epoch}: Violations = {violations}/{len(X)}")
        print("W:", [round(w, 5) for w in W])
        
    if violations == 0:
        print(f"Converged at epoch {epoch}!")
        break

print("Final W:", [round(w, 5) for w in W])

# Try to round the weights to nice numbers by scaling them so that W[1] (base_M) is exactly 0.5 or 1.0 or something.
# We know base_S = 0.
