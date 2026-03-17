import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

def get_stints(strat, total_laps):
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    
    for stop in stops:
        pit_lap = stop['lap']
        stint_len = pit_lap - current_lap + 1
        stints.append((current_tire, stint_len))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stint_len = total_laps - current_lap + 1
        stints.append((current_tire, stint_len))
        
    return stints

for race in races[:200]:
    config = race['race_config']
    strats = {s['driver_id']: s for _, s in race['strategies'].items()}
    finishing = race['finishing_positions']
    
    for i in range(len(finishing)):
        d1 = finishing[i]
        s1 = strats[d1]
        stints1 = get_stints(s1, config['total_laps'])
        
        # Did d1 run a huge soft stint?
        has_huge_soft = any(tire == 'SOFT' and length > 25 for tire, length in stints1)
        if has_huge_soft:
            # Let's find someone who beat them with identical pits but NO huge soft stint
            for j in range(i):
                d2 = finishing[j]
                s2 = strats[d2]
                stints2 = get_stints(s2, config['total_laps'])
                
                # Assume 1 pit stop
                if len(s1['pit_stops']) == 1 and len(s2['pit_stops']) == 1:
                    if not any(tire == 'SOFT' and length > 25 for tire, length in stints2):
                        # Calculate total Soft/Medium/Hard laps
                        s1_laps = {'SOFT': 0, 'MEDIUM': 0, 'HARD': 0}
                        for t, l in stints1: s1_laps[t] += l
                            
                        s2_laps = {'SOFT': 0, 'MEDIUM': 0, 'HARD': 0}
                        for t, l in stints2: s2_laps[t] += l
                        
                        # If D2 ran FEWER soft laps but BEAT D1, the cliff is real!
                        if s2_laps['SOFT'] < s1_laps['SOFT'] and s2_laps['HARD'] >= s1_laps['HARD']:
                            print(f"{d2} (Rank {j}) BEAT {d1} (Rank {i}) despite fewer soft laps!")
                            print(f"D1 {d1} (loser): {stints1}")
                            print(f"D2 {d2} (winner): {stints2}")
                            print("-" * 40)
                            break
                            
