import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

best_temp = 32
valid_races = [r for r in races if r['race_config']['track_temp'] == best_temp]

print("--- Races 1 to 33 ---")
tracks_seen = set()
for i in range(33):
    r = valid_races[i]
    track = r['race_config']['track']
    tracks_seen.add(track)
    print(f"Race {i+1}: Track={track}, Laps={r['race_config']['total_laps']}, BLT={r['race_config']['base_lap_time']}, PLT={r['race_config']['pit_lane_time']}")

print("\n--- Race 34 ---")
r34 = valid_races[33]
track34 = r34['race_config']['track']
print(f"Race 34: Track={track34}, Laps={r34['race_config']['total_laps']}, BLT={r34['race_config']['base_lap_time']}, PLT={r34['race_config']['pit_lane_time']}")

print(f"\nIs Track 34 new? {track34 not in tracks_seen}")

