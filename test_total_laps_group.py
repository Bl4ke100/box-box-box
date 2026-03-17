import numpy as np
from scipy.optimize import linprog
import json
import glob
import os

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

c_idx_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2}

def get_feats_arr_add(race_config, strat):
    features = np.zeros(225)
    total_laps = race_config['total_laps']
    current_lap = 1
    current_tire = strat['starting_tire']
    stops = strat['pit_stops']
    
    stints = []
    for stop in stops:
        pit_lap = stop['lap']
        stints.append((current_tire, pit_lap - current_lap + 1))
        current_lap = pit_lap + 1
        current_tire = stop['to_tire']
        
    if current_lap <= total_laps:
        stints.append((current_tire, total_laps - current_lap + 1))
        
    for tire, slen in stints:
        c_idx = c_idx_map[tire]
        for age in range(1, slen + 1):
            features[c_idx * 75 + age - 1] += 1
                
    return features


def test_group(races_group, multiplicative=False):
    A_diff = []
    C_diff = []
    
    for idx, race in enumerate(races_group):
        config = race['race_config']
        strats = {s['driver_id']: s for _, s in race['strategies'].items()}
        finishing = race['finishing_positions']
        plt = config['pit_lane_time']
        blt = config['base_lap_time']
        
        race_A = []
        race_C = []
        
        for i in range(len(finishing) - 1):
            d1 = finishing[i]
            d2 = finishing[i+1]
            
            f1 = get_feats_arr_add(config, strats[d1])
            f2 = get_feats_arr_add(config, strats[d2])
            
            if multiplicative:
                f1 *= blt
                f2 *= blt
            
            c1 = plt * len(strats[d1]['pit_stops'])
            c2 = plt * len(strats[d2]['pit_stops'])
            
            diff_f = f1 - f2
            diff_C = c1 - c2
            
            if not (np.all(np.abs(diff_f) < 0.001) and abs(diff_C) < 0.001):
                race_A.append(diff_f)
                race_C.append(diff_C)
                
        A_diff.extend(race_A)
        C_diff.extend(race_C)
    
    A = np.array(A_diff)
    C = np.array(C_diff)
    
    c = np.zeros(225)
    b_ub = -C
    
    A_mono = []
    for c_id in range(3):
        for age in range(74):
            row = np.zeros(225)
            row[c_id * 75 + age] = 1
            row[c_id * 75 + age + 1] = -1
            A_mono.append(row)
            
    A_mono = np.array(A_mono)
    b_mono = np.zeros(len(A_mono))
    
    A_full = np.vstack([A, A_mono])
    b_full = np.hstack([b_ub, b_mono])
    bounds = [(None, None)] * 225
    
    res = linprog(c, A_ub=A_full, b_ub=b_full, bounds=bounds, method='highs')
    return res.success

# Let's test group: Temp = 32, Total Laps = 50
group = [r for r in races if r['race_config']['track_temp'] == 32 and r['race_config']['total_laps'] == 50]

print(f"Found {len(group)} races for Temp=32, Laps=50")
print("Additive Success:", test_group(group, multiplicative=False))
print("Multiplicative Success:", test_group(group, multiplicative=True))

# Let's test group: Temp = 32, BLT = 82 (round to nearest int)
group2 = [r for r in races if r['race_config']['track_temp'] == 32 and int(r['race_config']['base_lap_time']) == 82]
print(f"Found {len(group2)} races for Temp=32, int(BLT)=82")
print("Additive Success:", test_group(group2, multiplicative=False))
print("Multiplicative Success:", test_group(group2, multiplicative=True))

