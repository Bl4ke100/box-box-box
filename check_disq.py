import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:2]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

violations = 0
for race in races[:200]:
    strategies = race['strategies']
    finishing = race['finishing_positions']
    
    for rank, d_id in enumerate(finishing):
        strat = strategies[f"pos{int(d_id[1:])}"] # wait, strategies key is "pos1", driver_id is inside.
        
        # better: find by driver_id
        for key, s in strategies.items():
            if s['driver_id'] == d_id:
                strat = s
                break
                
        compounds = set([strat['starting_tire']])
        for p in strat['pit_stops']:
            compounds.add(p['to_tire'])
            
        if len(compounds) < 2:
            print(f"Driver {d_id} used {len(compounds)} compounds. Rank: {rank+1}/20")
            violations += 1

print(f"Total 1-compound drivers: {violations}")

