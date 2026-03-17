import json
import os
import glob
import math

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

print(f"Loaded {len(races)} races.")

def extract_features(race_config, strat):
    # Returns [b_s, b_m, b_h, d_s, d_m, d_h, t_s, t_m, t_h], constant_time
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

# Build pairs of inequalities: feat_diff * W + const_diff <= -margin
# feat_diff = f_i - f_{i+1}
# const_diff = c_i - c_{i+1}
F_diff = []
C_diff = []

for race in races:
    config = race['race_config']
    strats = {}
    for pos_key, strat in race['strategies'].items():
        strats[strat['driver_id']] = strat
        
    finishing = race['finishing_positions']
    driver_features = {}
    driver_const = {}
    
    for d_id in finishing:
        feats, const = extract_features(config, strats[d_id])
        driver_features[d_id] = feats
        driver_const[d_id] = const
        
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1 = driver_features[d1]
        c1 = driver_const[d1]
        
        f2 = driver_features[d2]
        c2 = driver_const[d2]
        
        fdiff = [x - y for x, y in zip(f1, f2)]
        cdiff = c1 - c2
        
        F_diff.append(fdiff)
        C_diff.append(cdiff)

print(f"Constructed {len(F_diff)} inequalities.")

# Gradient descent
W = [0.0] * 9
learning_rate = 0.0001
epochs = 500
margin = 0.5 

for epoch in range(epochs):
    loss = 0.0
    grads = [0.0] * 9
    violations = 0
    
    for fdiff, cdiff in zip(F_diff, C_diff):
        val = sum(w * x for w, x in zip(W, fdiff)) + cdiff
        if val > -margin:
            # Violation: val should be <= -margin
            loss += val + margin
            violations += 1
            for j in range(9):
                grads[j] += fdiff[j]
                
    if epoch % 50 == 0:
        print(f"Epoch {epoch}: Loss = {loss:.4f}, Violations = {violations}/{len(F_diff)}")
        print("W:", [round(x, 4) for x in W])
        
    if violations == 0:
        print(f"Converged at epoch {epoch}!")
        break
        
    for j in range(9):
        W[j] -= learning_rate * grads[j] / len(F_diff)
        if W[j] < 0:
            W[j] = 0.0  # project to positive orthant

print("Final W:", [round(x, 4) for x in W])

# Output the predicted total times using the final W for the first race
race0 = races[0]
config = race0['race_config']
strats = {s['driver_id']: s for _, s in race0['strategies'].items()}
predicted_times = []
for d_id in race0['finishing_positions']:
    feats, const = extract_features(config, strats[d_id])
    tot = sum(w * x for w, x in zip(W, feats)) + const
    predicted_times.append((tot, d_id))

print("Original order vs Predicted order:")
for i, d in enumerate(race0['finishing_positions']):
    print(f"{i+1:2d}. {d}")
    
predicted_times.sort()
print("\Predicted Model Order:")
for i, (t, d) in enumerate(predicted_times):
    print(f"{i+1:2d}. {d} (Time: {t:.2f})")
    
