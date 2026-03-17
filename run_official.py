"""Run all 100 test cases through the official race_simulator.py"""
import subprocess
import json
import glob
import os

test_cases_dir = r"data/test_cases/inputs"
expected_dir = r"data/test_cases/expected_outputs"

test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
passed = 0
failed_tests = []

for f in test_files:
    name = os.path.basename(f)
    result = subprocess.run(
        ["python", "solution/race_simulator.py", f],
        capture_output=True, text=True
    )
    pred = json.loads(result.stdout)['finishing_positions']
    exp = json.load(open(os.path.join(expected_dir, name)))['finishing_positions']
    if pred == exp:
        passed += 1
    else:
        diffs = [(i, exp[i], pred[i]) for i in range(20) if exp[i] != pred[i]][:3]
        failed_tests.append((name, diffs))

print(f"OFFICIAL RESULTS: {passed}/100 ({passed}%)")
if failed_tests:
    print(f"\nFailing tests:")
    for name, diffs in failed_tests:
        print(f"  {name}: {diffs}")
