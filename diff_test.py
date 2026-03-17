import json, glob, os
import final_test_runner as ftr

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
        test_data.append((t, rank_map, name))
    return test_data

for t, e_map, name in load_data():
    tid = t['race_id'].lower() + '.json'
    predicted = ftr.manual_sim(r'data/test_cases/inputs/' + tid)
    expected = [k for k, v in sorted(e_map.items(), key=lambda x: x[1])]
    if predicted != expected:
        # Find first and last swapped positions
        diffs = [(i, expected[i], predicted[i]) for i in range(20) if expected[i] != predicted[i]]
        print(f"\n{name} (T={t['race_config']['track_temp']}):")
        for idx, exp_d, got_d in diffs[:3]:
            print(f"  Pos {idx+1}: expected {exp_d}, got {got_d}")
