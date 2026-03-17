import json

# exact manual calculation for test_011
t = json.load(open('data/test_cases/inputs/test_011.json'))
config = t['race_config']
blt = config['base_lap_time']
plt = config['pit_lane_time']
temp = config['track_temp']
total_laps = config['total_laps']
print(f"BLT={blt}, PLT={plt}, Temp={temp}, Laps={total_laps}")

# Get temp_map params for T=33
tm = json.load(open('temp_map.json'))
p = tm['33']
c_s, c_h = p[0], p[1]
d_s, d_m, d_h = p[2], p[3], p[4]
print(f"c_s={c_s:.6f}, c_h={c_h:.6f}, d_s={d_s:.6f}, d_m={d_m:.6f}, d_h={d_h:.6f}")

# D004: HARD(26), MEDIUM(27) - 1 pit stop at lap 26
# D007: MEDIUM(27), HARD(26) - 1 pit stop at lap 27
th = {'SOFT': 10, 'MEDIUM': 20, 'HARD': 30}

def calc_time(stints, label):
    time = plt * 1  # 1 pit stop
    for tire, slen in stints:
        c = c_s if tire == 'SOFT' else 0.0 if tire == 'MEDIUM' else c_h
        dr = d_s if tire == 'SOFT' else d_m if tire == 'MEDIUM' else d_h
        th_val = th[tire]
        time += (blt + c) * slen
        K = max(0, slen - th_val)
        time += (K*(K+1)/2) * blt * dr
    print(f"{label}: time={time:.8f}")
    return time

t4 = calc_time([('HARD', 26), ('MEDIUM', 27)], 'D004')
t7 = calc_time([('MEDIUM', 27), ('HARD', 26)], 'D007')
print(f"Diff (D004-D007): {t4-t7:.8f}")

# Now let's use EXACT integers -1.0 and 0.8 and standard 0.0198, 0.01, 0.005 * 1.0 (T=33 is warm)
print("\n--- With EXACT step-function params (Warm: d_s=0.0198, d_m=0.01, d_h=0.005) ---")
def calc_time2(stints, label, c_s2=-1.0, c_h2=0.8, d_s2=0.0198, d_m2=0.01, d_h2=0.005):
    time = plt * 1
    for tire, slen in stints:
        c = c_s2 if tire == 'SOFT' else 0.0 if tire == 'MEDIUM' else c_h2
        dr = d_s2 if tire == 'SOFT' else d_m2 if tire == 'MEDIUM' else d_h2
        th_val = th[tire]
        time += (blt + c) * slen
        K = max(0, slen - th_val)
        time += (K*(K+1)/2) * blt * dr
    print(f"{label}: time={time:.8f}")
    return time

t4b = calc_time2([('HARD', 26), ('MEDIUM', 27)], 'D004')
t7b = calc_time2([('MEDIUM', 27), ('HARD', 26)], 'D007')
print(f"Diff (D004-D007): {t4b-t7b:.8f}")

# The expected ordering is D004 before D007, so D004 must have LOWER time
# Let's find what D_H would make D004 < D007
print(f"\nFor D004 to beat D007, we need D004_time < D007_time")
print(f"Both use same number of H and M laps (26 H, 27 M)")
print(f"Difference comes from: when the IPP kicks in (before lap 30 for HARD, before lap 20 for MEDIUM)")
print(f"D004 runs HARD first (26 laps, no deg since 26 <= 30), then MEDIUM (27 laps, 7 laps beyond 20)")
print(f"D007 runs MEDIUM first (27 laps, 7 laps beyond 20), then HARD (26 laps, no deg since 26 <= 30)")
print(f"So D004 time = PLT + (blt+c_h)*26 + (blt)*27 + 7*8/2*blt*d_m")
print(f"D007 time = PLT + (blt)*27 + 7*8/2*blt*d_m + (blt+c_h)*26")
print(f"They are EXACTLY equal algebraically! Difference is 0.")
print(f"This means they genuinely tie and the tiebreaker is purely based on externals (grid pos, alphabetical, etc.)")
