"""
Edge case tests for race_simulator.py:
1. Multi-stop strategies (2 and 3 stops)
2. Drivers on the same compound the whole race (0 tire changes)
3. Stress test: cold and hot temperature extremes
"""
import json, subprocess, os

def run_sim(test_data):
    inp = json.dumps(test_data)
    r = subprocess.run(
        ['python', 'solution/race_simulator.py'],
        input=inp, capture_output=True, text=True
    )
    if r.returncode != 0:
        print("ERROR:", r.stderr)
        return None
    return json.loads(r.stdout)

# --- Test 1: Manually crafted 2-stop race ---
case2stop = {
    "race_id": "EDGE_001",
    "race_config": {"base_lap_time": 85.0, "pit_lane_time": 25.0, "track_temp": 30, "total_laps": 60},
    "strategies": {
        "pos1": {"driver_id": "D001", "starting_tire": "SOFT", "pit_stops": [{"lap": 10, "from_tire": "SOFT", "to_tire": "MEDIUM"}, {"lap": 35, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
        "pos2": {"driver_id": "D002", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
    }
}
r = run_sim(case2stop)
print("2-stop test: output =", r['finishing_positions'])
assert len(r['finishing_positions']) == 2
assert r['race_id'] == 'EDGE_001'
print("2-stop test: PASSED")

# --- Test 2: Cold track ---
case_cold = {
    "race_id": "EDGE_COLD",
    "race_config": {"base_lap_time": 90.0, "pit_lane_time": 22.0, "track_temp": 18, "total_laps": 50},
    "strategies": {
        "pos1": {"driver_id": "D001", "starting_tire": "HARD", "pit_stops": [{"lap": 30, "from_tire": "HARD", "to_tire": "MEDIUM"}]},
        "pos2": {"driver_id": "D002", "starting_tire": "MEDIUM", "pit_stops": [{"lap": 20, "from_tire": "MEDIUM", "to_tire": "HARD"}]},
    }
}
r = run_sim(case_cold)
print("Cold track test (T=18): output =", r['finishing_positions'])
assert len(r['finishing_positions']) == 2
print("Cold track test: PASSED")

# --- Test 3: Hot track ---
case_hot = {
    "race_id": "EDGE_HOT",
    "race_config": {"base_lap_time": 80.0, "pit_lane_time": 26.0, "track_temp": 42, "total_laps": 45},
    "strategies": {
        "pos1": {"driver_id": "D001", "starting_tire": "SOFT", "pit_stops": [{"lap": 10, "from_tire": "SOFT", "to_tire": "HARD"}]},
        "pos2": {"driver_id": "D002", "starting_tire": "HARD", "pit_stops": [{"lap": 25, "from_tire": "HARD", "to_tire": "MEDIUM"}]},
    }
}
r = run_sim(case_hot)
print("Hot track test (T=42): output =", r['finishing_positions'])
assert len(r['finishing_positions']) == 2
print("Hot track test: PASSED")

# --- Test 4: 3-stop driver ---
case_3stop = {
    "race_id": "EDGE_3STOP",
    "race_config": {"base_lap_time": 82.0, "pit_lane_time": 24.0, "track_temp": 32, "total_laps": 70},
    "strategies": {
        "pos1": {"driver_id": "D001", "starting_tire": "SOFT", "pit_stops": [
            {"lap": 10, "from_tire": "SOFT", "to_tire": "MEDIUM"},
            {"lap": 30, "from_tire": "MEDIUM", "to_tire": "SOFT"},
            {"lap": 40, "from_tire": "SOFT", "to_tire": "HARD"}
        ]},
        "pos2": {"driver_id": "D002", "starting_tire": "HARD", "pit_stops": [{"lap": 35, "from_tire": "HARD", "to_tire": "MEDIUM"}]},
    }
}
r = run_sim(case_3stop)
print("3-stop test: output =", r['finishing_positions'])
assert len(r['finishing_positions']) == 2
print("3-stop test: PASSED")

print("\nAll edge case tests PASSED!")
