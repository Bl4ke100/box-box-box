import numpy as np
from scipy.optimize import linprog

# Test if constraints 10 and 11 ALONE are contradictory!

# Diff F order: S_laps, M_laps, H_laps, S_age, M_age, H_age, S_temp, M_temp, H_temp
# Temp = 27 for both equations. We can just use the exact diff_f values provided.

c10_f = np.array([-1.0, -33.0, 34.0, -17.0, -561.0, 307.0, -459.0, -15147.0, 8289.0])
c10_c = np.array(22.699999999999818)

c11_f = np.array([2.0, -2.0, 0.0, 33.0, -69.0, 0.0, 891.0, -1863.0, 0.0])
c11_c = np.array(0.0)

A = np.vstack([c10_f, c11_f])
b = np.array([-c10_c - 0.01, -c11_c - 0.01])

c = np.zeros(9)
bounds = [(None, None)] * 9
bounds[0] = (0.0, 0.0) # S base = 0

print("Testing only constraints 10 and 11...")
res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
print("Status:", res.status, "Message:", res.message)

# If it's feasible, add Constraint 9
# Constraint 9: D007 beats D012
c9_f = np.array([0.0, 19.0, -19.0, 0.0, 190.0, -187.0, 0.0, 5130.0, -5049.0])
c9_c = np.array(0.0)

A = np.vstack([c9_f, c10_f, c11_f])
b = np.array([-c9_c - 0.01, -c10_c - 0.01, -c11_c - 0.01])

print("\nTesting constraints 9, 10, 11...")
res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
print("Status:", res.status, "Message:", res.message)

