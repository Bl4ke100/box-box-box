import json
t = json.load(open('data/test_cases/inputs/test_011.json'))
print('Temp:', t['race_config']['track_temp'])
for s in t['strategies'].values():
    if s['driver_id'] in ['D004', 'D007']:
        print(s['driver_id'], ':', s['starting_tire'], '->', [(x['lap'], x['to_tire']) for x in s['pit_stops']])
