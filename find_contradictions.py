import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_feats(race_config, strat):
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

# We'll use the exactly solved parameters to predict all 1000 races' 19000 pairs.
# Then we'll print out the TOP 5 most violated pairs, and examine their exact strategies by hand.
W = [0.0, 1.288798126921987, 2.230242290510759, 
     0.28932164604769256, 0.11319510134007353, 0.04675074851855996, 
     0.0014809653875818654, 0.0007285830032904396, 0.000379987873841571]

violations = []

for race in races[:100]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        f1, c1 = get_feats(config, strats[d1])
        f2, c2 = get_feats(config, strats[d2])
        
        t1 = sum(w * x for w, x in zip(W, f1)) + c1
        t2 = sum(w * x for w, x in zip(W, f2)) + c2
        
        if t1 > t2:
            # Violation! t1 should be < t2
            diff = t1 - t2
            violations.append((diff, config, d1, d2, strats[d1], strats[d2], t1, t2))

violations.sort(reverse=True, key=lambda x: x[0])

print(f"Total pairs: {100 * 19}, Violations: {len(violations)}")
print("Top 3 Violations:")

for i in range(3):
    diff, config, d1, d2, s1, s2, t1, t2 = violations[i]
    print(f"\n--- Violation {i+1} : Predicted {d1} ({t1:.2f}) > {d2} ({t2:.2f}) by {diff:.2f}s ---")
    print(f"Track: {config['track']}, Laps: {config['total_laps']}, Temp: {config['track_temp']}, Base: {config['base_lap_time']}, Pit: {config['pit_lane_time']}")
    print(f"{d1} (True Pos Winner): {s1['starting_tire']} -> {s1['pit_stops']}")
    print(f"{d2} (True Pos Loser) : {s2['starting_tire']} -> {s2['pit_stops']}")

