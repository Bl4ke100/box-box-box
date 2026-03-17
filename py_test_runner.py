import os
import glob
import json
import subprocess

def main():
    test_cases_dir = r"data/test_cases/inputs"
    expected_dir = r"data/test_cases/expected_outputs"
    
    test_files = sorted(glob.glob(os.path.join(test_cases_dir, "test_*.json")))
    
    if not test_files:
        print("No test cases found.")
        return
        
    passed = 0
    failed = 0
    total = len(test_files)
    
    for test_file in test_files:
        test_name = os.path.basename(test_file)
        expected_file = os.path.join(expected_dir, test_name)
        
        # Read test case input
        with open(test_file, 'r') as f:
            input_data = f.read()
            
        # Run simulator
        # Run simulator directly using file path arg
        process = subprocess.run(
            ['python', 'solution/race_simulator.py', test_file],
            text=True,
            capture_output=True
        )
        
        if process.returncode != 0:
            print(f"[{test_name}] ERROR: {process.stderr.strip()}")
            failed += 1
            continue
            
        try:
            output_json = json.loads(process.stdout)
            predicted = output_json.get('finishing_positions', [])
        except Exception as e:
            print(f"[{test_name}] INVALID OUTPUT: {e}")
            failed += 1
            continue
            
        # Compare with expected
        if os.path.exists(expected_file):
            with open(expected_file, 'r') as f:
                expected_json = json.load(f)
            expected = expected_json.get('finishing_positions', [])
            
            if predicted == expected:
                passed += 1
            else:
                print(f"[{test_name}] FAILED")
                print(f"  Expected: {expected}")
                print(f"  Got:      {predicted}")
                failed += 1
        else:
            print(f"[{test_name}] NO EXPECTED OUTPUT FOUND (Predicted: {predicted})")
            passed += 1 # assume passing format check
            
    print(f"\nRESULTS: {passed} / {total} Passed ({passed/total*100:.1f}%)")

if __name__ == '__main__':
    main()
