import math
import config
import matplotlib.pyplot as plt
from dynamicBearing.feature import prepare_features
from dynamicBearing.filling import FillSet

def simulate_v_by_static(max_v: float, duration: float):
    
    ves = []
    vos = []
    
    # Initialize ves and vos
    for t in range(duration):
        if t <= 120:
            ves.append(60)
            vos.append(0)
        elif t <= 640:
            ves.append(max_v)
            vos.append(30)
        else:
            ves.append(0)
            vos.append(120)
    
    return [(ves[i] - vos[i]) for i in range (len(ves))]

def simulate_v_by_sin_power_x(max_v: float, T: float):
    
    # v = ve - vo
    # ve: Entry Velocities / Minute
    # vo: Output Velocities / Minute
    
    x = 1
    vs: list[float] = []
    for t in range (T):
        v = abs(max_v * math.pow(math.sin(t * 2 * math.pi / T), x))
        if t > T / 2.0:
            v *= -1.0
        vs.append(v)
    
    return vs

def simulate_dangerous_situation(v_func, duration: float):
    
    max_v = 0
    while True:
        
        vs = v_func(max_v, duration)
        
        FN = FillSet(features).execute(vs, duration)
        
        dangerous = False
        for t, db in enumerate(FN.dbs):
            if db >= FN.sb and t < duration / 4:
                dangerous = True
                FN.show_plot()
                print('\n\n========= Dangerous Max Velocity Situation =========\n\n')
                print(f'Max velocity = {max_v + 1}\n\n')
                print('====== Static Bearing Capacity Reached Time ======\n\n')
                print(f'Reaching Time: {t}\n\n')
                print('====== Dangerous Dynamic Bearing Capacity Simulation ======\n\n')
                print([int(db) for db in FN.dbs])
                break
        
        if dangerous:
            break
        max_v += 1
    
    vs = v_func(max_v, duration)
    FN = FillSet(features).execute(vs, duration)
    FN.show_result()
    plt.plot(vs, FN.dbs)
    plt.xlabel('v')
    plt.ylabel('Dynamic Bearing Capacity')
    plt.grid(True)
    plt.show()
    

if __name__ == '__main__':
    
    # Read shapefiles and parse line or polygon features 
    features = prepare_features([[config.DIR_RESOURCE_LINE, 'Line'], [config.DIR_RESOURCE_POLYGON, 'Polygon']])
    simulation_duration = 16 * 60 # From 8:00 AM to 24:00 PM
    
    simulate_dangerous_situation(simulate_v_by_sin_power_x, simulation_duration)
            