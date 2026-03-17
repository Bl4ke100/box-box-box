import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

valid_races = [r for r in races if r['race_config']['track'] == 'Suzuka' and r['race_config']['track_temp'] == 32]

for i in range(32):
    if i < len(valid_races):
        config = valid_races[i]['race_config']
        print(f"Suzuka {i+1}: L= {config['total_laps']}, BLT= {config['base_lap_time']}, PLT= {config['pit_lane_time']}")
