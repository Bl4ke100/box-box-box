import json
test_case = json.load(open('data/test_cases/inputs/test_003.json'))
expected = json.load(open('data/test_cases/expected_outputs/test_003.json'))['finishing_positions']

try:
    print("D011 rank:", expected.index('D011') + 1)
except: pass
try:
    print("D013 rank:", expected.index('D013') + 1)
except: pass
