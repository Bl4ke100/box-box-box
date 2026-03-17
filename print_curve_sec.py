import json
from scipy.optimize import linprog

def extract_curve_for_race():
    with open('data/historical_races/race_00000.json') as f:
        races = json.load(f)
    race = races[0] # Just one race
    temp = race['race_config']['track_temp']
    blt = race['race_config']['base_lap_time']
    plt = race['race_config']['pit_lane_time']
    strats = race['strategies']
    
    # Let's print the actual math if I just want to see the exact time progression?
    # I can't from a single race because I only have Total Times!
    # I previously used print_full_curve.py which solved linear equations!
    # Let's just print D011 and D013 full manual evaluation to see where the 58s went.
    pass

if __name__ == '__main__':
    print("Cannot extract Lap Times cleanly without solver! Running LP to see deg curve")
