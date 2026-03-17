import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
with open(files[0], 'r') as fin:
    races.extend(json.load(fin))

def get_total_time(race_config, strat, params):
    total_laps = race_config['total_laps']
    temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    
    constant_time = base_lap_time * total_laps + pit_lane_time * len(strat['pit_stops'])
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    var_time = 0.0
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        sum_age = stint_len * (stint_len + 1) / 2
        
        b = params[f"base_{current_tire[0]}"]
        d = params[f"deg_{current_tire[0]}"]
        t = params[f"temp_{current_tire[0]}"]
        
        var_time += b * stint_len + d * sum_age + t * sum_age * temp
        
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        sum_age = stint_len * (stint_len + 1) / 2
        
        b = params[f"base_{current_tire[0]}"]
        d = params[f"deg_{current_tire[0]}"]
        t = params[f"temp_{current_tire[0]}"]
        
        var_time += b * stint_len + d * sum_age + t * sum_age * temp
        
    return constant_time + var_time

params_rounded = {
  "base_S": 0.0,
  "base_M": 1.3,
  "base_H": 2.2,
  "deg_S": 0.3,
  "deg_M": 0.1,
  "deg_H": 0.05,
  "temp_S": 0.0015,
  "temp_M": 0.00075,
  "temp_H": 0.0004
}

race = races[0]
config = race['race_config']
strats = {s['driver_id']: s for _, s in race['strategies'].items()}
finishing = race['finishing_positions']

predictions = []
for d_id in finishing:
    t = get_total_time(config, strats[d_id], params_rounded)
    predictions.append((t, d_id))

predictions.sort()
predicted_order = [p[1] for p in predictions]

print("Finishing (ground truth):")
print(finishing)
print("\nPredicted order:")
print(predicted_order)

print("\nAccuracy on single:", finishing == predicted_order)

