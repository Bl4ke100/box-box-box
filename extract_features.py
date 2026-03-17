import json
import os
import glob
from collections import defaultdict

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:1]:  # Just load the first file for now (1000 races)
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

print(f"Loaded {len(races)} races.")

# Let's see if we can find races where cars use the same strategy but pit on different laps.
# Or let's just dump the config and strategies for the first race and the finishing positions to analyze manually.

race = races[0]
print("Race Config:", race['race_config'])
print("Finishing Positions:", race['finishing_positions'])
for i, pos in enumerate(race['finishing_positions']):
    for key, strat in race['strategies'].items():
        if strat['driver_id'] == pos:
            print(f"{i+1:2d}. {pos} - {strat['starting_tire']} -> " + 
                  " -> ".join([f"Pit L{p['lap']} ({p['to_tire']})" for p in strat['pit_stops']]))

# Let's analyze simple 1-stop strategies.
print("\n--- Analysing 1-stop strategies across races ---")
for r in races[:10]:
    config = r['race_config']
    print(f"\nRace: {config['track']}, Laps: {config['total_laps']}, Base: {config['base_lap_time']}, Temp: {config['track_temp']}")
    
    strats = []
    for pos in r['finishing_positions']:
        for key, strat in r['strategies'].items():
            if strat['driver_id'] == pos:
                strats.append(strat)
                break
    
    for i, s in enumerate(strats):
        stops = s['pit_stops']
        if len(stops) == 1:
            print(f"{i+1:2d}. {s['starting_tire']} to L{stops[0]['lap']} then {stops[0]['to_tire']}")
    
