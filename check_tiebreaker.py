import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

with open(files[0], 'r') as fin:
    races = json.load(fin)

def get_feats(race_config, strat):
    total_laps = race_config['total_laps']
    pit_lane_time = race_config['pit_lane_time']
    base_lap_time = race_config['base_lap_time']
    features = [0.0] * 3
    
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        idx = 0 if current_tire == 'SOFT' else (1 if current_tire == 'MEDIUM' else 2)
        features[idx] += stint_len
        
    return features

tied = 0
correct_grid_sort = 0
correct_alpha_sort = 0

for race in races:
    config = race['race_config']
    
    # Store grid position integer, 1 to 20
    strats = {}
    for pos_key, s in race['strategies'].items():
        grid_pos = int(pos_key.replace('pos', ''))
        s['grid_pos'] = grid_pos
        strats[s['driver_id']] = s
        
    finishing = race['finishing_positions']
    
    for i in range(len(finishing) - 1):
        d1 = finishing[i]
        d2 = finishing[i+1]
        
        s1 = strats[d1]
        s2 = strats[d2]
        
        f1 = get_feats(config, s1)
        f2 = get_feats(config, s2)
        
        # Are they completely identical in lengths?
        if f1 == f2 and s1['starting_tire'] == s2['starting_tire'] and len(s1['pit_stops']) == len(s2['pit_stops']):
            # Verify actual identical pit stops
            identical = True
            for p1, p2 in zip(s1['pit_stops'], s2['pit_stops']):
                if p1['lap'] != p2['lap'] or p1['to_tire'] != p2['to_tire']:
                    identical = False
            
            if identical:
                tied += 1
                grid1 = s1['grid_pos']
                grid2 = s2['grid_pos']
                
                # Check how they are sorted. They finished d1 BEFORE d2.
                if grid1 < grid2:
                    correct_grid_sort += 1
                    
                if d1 < d2:
                    correct_alpha_sort += 1

print(f"Total identically precise ties: {tied}")
print(f"Ties sorted by Original Grid Position: {correct_grid_sort} / {tied}")
print(f"Ties sorted by Alphabetical Driver ID: {correct_alpha_sort} / {tied}")

