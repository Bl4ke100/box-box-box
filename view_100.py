import json
t = json.load(open('data/test_cases/inputs/test_100.json'))
for s in t['strategies'].values():
    if s['driver_id'] in ['D001', 'D008']:
        print(s)
