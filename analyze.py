import json
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
if not files:
    print("No historical data found.")
    exit()

first_file = os.path.join(data_dir, files[0])
with open(first_file, 'r') as f:
    data = json.load(f)

print(f"Loaded {len(data)} races from {files[0]}")
if len(data) > 0:
    race = data[0]
    print(json.dumps(race, indent=2))
