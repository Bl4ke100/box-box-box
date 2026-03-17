import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

temps = set()
for race in races:
    temps.add(race['race_config']['track_temp'])

print("Unique track temps:", sorted(list(temps)))

