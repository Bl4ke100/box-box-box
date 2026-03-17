import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    # We want D020 vs D003
    if 'D020' in finishing and 'D003' in finishing:
        # Just find the specific race. It has temp=27, pit=22.7.
        if config['track_temp'] == 27 and abs(config['pit_lane_time'] - 22.7) < 0.1:
            print("Total Laps:", config['total_laps'])
            print("D020:")
            print(json.dumps(strats['D020'], indent=2))
            print("D003:")
            print(json.dumps(strats['D003'], indent=2))
            break
