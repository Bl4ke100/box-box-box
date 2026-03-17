import final_test_runner as ftr
import json, glob, os

def load_data():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    test_data = []
    
    for f_in in test_files:
        name = os.path.basename(f_in)
        f_exp = os.path.join(expected_dir, name)
        with open(f_in, 'r') as f: t = json.load(f)
        with open(f_exp, 'r') as f: e = json.load(f)
        expected_pos = e['finishing_positions']
        rank_map = {d: i for i, d in enumerate(expected_pos)}
        test_data.append((t, rank_map))
    return test_data

test_case = load_data()[5] # index 5 is test_006.json
t, e_map = test_case
name = t['race_id'].lower() + '.json'
predicted = ftr.manual_sim(r'data/test_cases/inputs/' + name)
e = [k for k, v in sorted(e_map.items(), key=lambda item: item[1])]

print("Expected:", e)
print("Got:     ", predicted)
