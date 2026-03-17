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

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]

race34 = valid_races[33]
config = race34['race_config']
strats = {s['driver_id']: s for _, s in race34['strategies'].items()}

max_stint = 0
for d, strat in strats.items():
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stints.append(pit_lap - current_lap + 1)
        current_lap = pit_lap + 1
        
    if current_lap <= config['total_laps']:
        stints.append(config['total_laps'] - current_lap + 1)
        
    for s in stints:
        if s > max_stint:
            max_stint = s

print(f"Max stint in Race 34: {max_stint}")
print(f"Total laps in Race 34: {config['total_laps']}")
