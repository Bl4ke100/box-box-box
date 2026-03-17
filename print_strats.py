import json

with open("data/test_cases/inputs/test_002.json", 'r') as f:
    t = json.load(f)
    
strats = t['strategies']
for d_id in ['D008', 'D017', 'D002', 'D012', 'D019', 'D020']:
    for pos, s in strats.items():
        if s['driver_id'] == d_id:
            print(f"{d_id} ({pos}): {s}")
