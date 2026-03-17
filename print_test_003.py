import json
t = json.load(open('data/test_cases/inputs/test_003.json'))
print(t['race_config'])
for s in t['strategies'].values():
    if s['driver_id'] in ['D011', 'D013']:
        print(s)
