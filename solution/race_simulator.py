#!/usr/bin/env python3
"""
F1 Race Simulator
Predicts finishing positions based on tire strategies and race conditions.

Formula:
- Each lap's time = base_lap_time + compound_offset + degradation_penalty
- compound_offset: SOFT=-1.0, MEDIUM=0.0, HARD=0.8
- degradation_penalty = max(0, tire_age - initial_performance_period) * base_lap_time * deg_rate
- deg_rate scales with temperature: <25°C → 0.8x, 25-34°C → 1.0x, >34°C → 1.3x
- IPP (initial performance period): SOFT=10, MEDIUM=20, HARD=30 laps
- Pit stop cost = pit_lane_time per stop
- Tiebreaker: grid starting position (lower = wins)
"""
import json
import sys

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            test_case = json.load(f)
    else:
        test_case = json.load(sys.stdin)

    race_id = test_case['race_id']
    config = test_case['race_config']
    strats = test_case['strategies']

    blt = config['base_lap_time']
    plt = config['pit_lane_time']
    temp = config['track_temp']
    total_laps = config['total_laps']

    # Temperature multiplier for degradation rate
    if temp < 25:
        t_mult = 0.8
    elif temp <= 34:
        t_mult = 1.0
    else:
        t_mult = 1.3

    # Compound speed offset (seconds per lap)
    c_offset = {'SOFT': -1.0, 'MEDIUM': 0.0, 'HARD': 0.8}

    # Base degradation rate per lap beyond IPP (scaled by temperature)
    base_deg = {'SOFT': 0.019775, 'MEDIUM': 0.010003, 'HARD': 0.005055}
    deg_rate = {k: v * t_mult for k, v in base_deg.items()}

    # Initial performance period (laps before degradation starts)
    th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}

    driver_times = []

    for pos, s in strats.items():
        d_id = s['driver_id']

        # Build pit stop lookup: {lap: next_tire}
        pit_laps = {stop['lap']: stop['to_tire'] for stop in s['pit_stops']}

        current_tire = s['starting_tire']
        current_age = 1  # tire age starts at lap 1
        total_time = plt * len(s['pit_stops'])  # pit stop time

        # Simulate lap by lap
        for lap in range(1, total_laps + 1):
            # Calculate this lap's time
            deg = max(0, current_age - th[current_tire])
            lap_time = blt + c_offset[current_tire] + deg * blt * deg_rate[current_tire]
            total_time += lap_time

            # Process pit stop at end of this lap
            if lap in pit_laps:
                current_tire = pit_laps[lap]
                current_age = 1
            else:
                current_age += 1

        # Grid starting position (used as tiebreaker)
        grid_pos = int(pos.replace('pos', ''))
        driver_times.append((total_time, grid_pos, d_id))

    # Sort by total time (ascending), then grid position (ascending) for ties
    driver_times.sort(key=lambda x: (x[0], x[1]))

    finishing_positions = [d_id for _, _, d_id in driver_times]

    output = {
        'race_id': race_id,
        'finishing_positions': finishing_positions
    }

    print(json.dumps(output))

if __name__ == '__main__':
    main()
