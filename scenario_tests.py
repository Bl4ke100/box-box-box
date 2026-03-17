#!/usr/bin/env python3
"""
10 simple scenario tests for race_simulator.py
Each tests a clear, understandable case so results can be validated by eye.
"""
import json
import subprocess

def run(scenario):
    r = subprocess.run(
        ['python', 'solution/race_simulator.py'],
        input=json.dumps(scenario),
        capture_output=True, text=True
    )
    return json.loads(r.stdout)['finishing_positions']

scenarios = [

    # --- 1. All same strategy, sorted by grid position ---
    {
        "desc": "All MEDIUM->HARD, winner = best grid (D001)",
        "race_id": "S01",
        "race_config": {"track": "Test", "total_laps": 40, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "D001", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
            "pos2": {"driver_id": "D002", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
            "pos3": {"driver_id": "D003", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
        }
    },

    # --- 2. SOFT start clearly wins vs HARD start (short race, within IPP) ---
    {
        "desc": "SOFT (no deg) beats HARD (no deg) in short race",
        "race_id": "S02",
        "race_config": {"track": "Test", "total_laps": 20, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "DSOFT", "starting_tire": "SOFT", "pit_stops": []},
            "pos2": {"driver_id": "DHARD", "starting_tire": "HARD", "pit_stops": []},
        }
    },

    # --- 3. Extra pit stop = slower (even though on fresh tires) ---
    {
        "desc": "1-stop beats 2-stop (extra pit = too costly)",
        "race_id": "S03",
        "race_config": {"track": "Test", "total_laps": 40, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "D1STOP", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
            "pos2": {"driver_id": "D2STOP", "starting_tire": "SOFT",   "pit_stops": [
                {"lap": 10, "from_tire": "SOFT",   "to_tire": "MEDIUM"},
                {"lap": 25, "from_tire": "MEDIUM", "to_tire": "HARD"}
            ]},
        }
    },

    # --- 4. Temperature effect: cold (0.8x deg) = less penalty ---
    {
        "desc": "Cold track (T=20): long SOFT stint works fine (low deg)",
        "race_id": "S04",
        "race_config": {"track": "Test", "total_laps": 40, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 20},
        "strategies": {
            "pos1": {"driver_id": "DLONG", "starting_tire": "SOFT", "pit_stops": [{"lap": 30, "from_tire": "SOFT", "to_tire": "MEDIUM"}]},
            "pos2": {"driver_id": "DEARLY","starting_tire": "SOFT", "pit_stops": [{"lap": 10, "from_tire": "SOFT", "to_tire": "MEDIUM"}]},
        }
    },

    # --- 5. Hot track (1.3x deg): early stop to avoid heavy degradation ---
    {
        "desc": "Hot track (T=40): early pit avoids heavy soft deg, beats late pitter",
        "race_id": "S05",
        "race_config": {"track": "Test", "total_laps": 40, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 40},
        "strategies": {
            "pos1": {"driver_id": "DEARLY","starting_tire": "SOFT", "pit_stops": [{"lap": 10, "from_tire": "SOFT", "to_tire": "HARD"}]},
            "pos2": {"driver_id": "DLATE", "starting_tire": "SOFT", "pit_stops": [{"lap": 30, "from_tire": "SOFT", "to_tire": "HARD"}]},
        }
    },

    # --- 6. HARD-only no pit: saves pit cost but pays with offset each lap ---
    {
        "desc": "No pit (HARD only) vs 1-stop SOFT->MEDIUM",
        "race_id": "S06",
        "race_config": {"track": "Test", "total_laps": 50, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "DNOPT", "starting_tire": "HARD", "pit_stops": []},
            "pos2": {"driver_id": "D1STOP","starting_tire": "SOFT", "pit_stops": [{"lap": 15, "from_tire": "SOFT", "to_tire": "HARD"}]},
        }
    },

    # --- 7. 3-driver race: SOFT->HARD, MEDIUM->HARD, HARD only ---
    {
        "desc": "3-car field: SOFT->HARD, MED->HARD, HARD-only",
        "race_id": "S07",
        "race_config": {"track": "Test", "total_laps": 50, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "DSH", "starting_tire": "SOFT",   "pit_stops": [{"lap": 10, "from_tire": "SOFT",   "to_tire": "HARD"}]},
            "pos2": {"driver_id": "DMH", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
            "pos3": {"driver_id": "DH",  "starting_tire": "HARD",   "pit_stops": []},
        }
    },

    # --- 8. Pit stop timing: same strategy, different pit lap ---
    {
        "desc": "Same SOFT->MED strategy, optimal pit timing matters",
        "race_id": "S08",
        "race_config": {"track": "Test", "total_laps": 50, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30},
        "strategies": {
            "pos1": {"driver_id": "DLAP10", "starting_tire": "SOFT", "pit_stops": [{"lap": 10, "from_tire": "SOFT", "to_tire": "MEDIUM"}]},
            "pos2": {"driver_id": "DLAP15", "starting_tire": "SOFT", "pit_stops": [{"lap": 15, "from_tire": "SOFT", "to_tire": "MEDIUM"}]},
            "pos3": {"driver_id": "DLAP20", "starting_tire": "SOFT", "pit_stops": [{"lap": 20, "from_tire": "SOFT", "to_tire": "MEDIUM"}]},
        }
    },

    # --- 9. Longer race: degradation matters more ---
    {
        "desc": "70-lap race: excessive SOFT deg punishes late pitter badly",
        "race_id": "S09",
        "race_config": {"track": "Test", "total_laps": 70, "base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 35},
        "strategies": {
            "pos1": {"driver_id": "DSMART", "starting_tire": "SOFT",   "pit_stops": [{"lap": 10, "from_tire": "SOFT",   "to_tire": "HARD"}]},
            "pos2": {"driver_id": "DSLOW",  "starting_tire": "SOFT",   "pit_stops": [{"lap": 40, "from_tire": "SOFT",   "to_tire": "HARD"}]},
        }
    },

    # --- 10. Real test case passthrough ---
    None  # filled in below from test_001.json
]

import glob, os
real_test = json.load(open('data/test_cases/inputs/test_001.json'))
real_expected = json.load(open('data/test_cases/expected_outputs/test_001.json'))['finishing_positions']
scenarios[9] = real_test
scenarios[9]['desc'] = f"Real test_001.json (expected: {real_expected[:3]}...)"

print("=" * 70)
print("    10 SCENARIO TESTS — race_simulator.py")
print("=" * 70)

for i, s in enumerate(scenarios, 1):
    desc = s.pop('desc', f'Scenario {i}')
    result = run(s)
    print(f"\n[{i:02d}] {desc}")
    if i == 10:
        match = result == real_expected
        print(f"     Result:   {result[:5]}...")
        print(f"     Expected: {real_expected[:5]}...")
        print(f"     ✅ MATCH" if match else "     ❌ MISMATCH")
    else:
        print(f"     Finishing order: {result}")
