import json
with open("data/test_cases/inputs/test_002.json", 'r') as f:
    t = json.load(f)

for pos, s in t['strategies'].items():
    if s['driver_id'] in ['D017', 'D008']:
        print(f"Driver: {s['driver_id']}")
        print(json.dumps(s, indent=2))
