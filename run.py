import math
import config
import matplotlib.pyplot as plt
from dbc.filling import FillSet
from dbc.feature import prepare_features

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

    return [(ves[i] - vos[i]) for i in range(len(ves))]


def simulate_v_by_sin_power_x(max_v: float, T: float):
    # v = ve - vo
    # ve: Entry Velocities / Minute
    # vo: Output Velocities / Minute

    x = 1
    vs: list[float] = []
    for t in range(T):
        v = abs(max_v * math.pow(math.sin(t * 2 * math.pi / T), x))
        if t > T / 2.0:
            v *= -1.0
        vs.append(v)

    return vs

# def simulate_seperate_ve_vo(t2: float, t3: float, n: float, v_max:float, duration: float):
    
#     ves = []
#     vos = []
#     for t in range(duration):
        
#         if t <= 120:
#             ves.append(t * v_max / t2)
#             vos.append(0)
#         elif t <= t2:
#             ves.append(t * v_max / t2)
#             vos.append(v_max / (t3 - 120) * t - 120 * v_max / (t3 - 120))
#         elif t<= t2 + n:
#             ves.append(v_max)
#             vos.append(v_max / (t3 - 120) * t - 120 * v_max / (t3 - 120))
#         elif t<= t3:
#             ves.append(v_max / (t2 + n - 960) * t - 960 * v_max / (t2 + n - 960))
#             vos.append(v_max / (t3 - 120) * t - 120 * v_max / (t3 - 120))
#         elif t<= 900:
#             ves.append(v_max / (t2 + n - 960) * t - 960 * v_max / (t2 + n - 960))
#             vos.append(v_max)
#         elif t<= 960:
#             ves.append(0)
#             vos.append(-v_max/60*t+15*v_max)

#     return [(ves[i] - vos[i]) for i in range(len(ves))]

def lerp(a: float, b: float, t: float):
    return (1 - t) * a + t * b

def normal_f(_min: float, _max: float, a: float):
    
    return (a - _min) / (_max - _min)

def simulate_seperate_ve_vo(t2: float, t3: float, n: float, v_max:float, duration: float):
    
    ves = []
    vos = []
    for t in range(duration):
        
        if t <= 120:
            ves.append(lerp(0, v_max, normal_f(0, t2, t)))
            vos.append(0)
            
        elif t <= t2:
            ves.append(lerp(0, v_max, normal_f(0, t2, t)))
            vos.append(lerp(0, v_max, normal_f(120, t3, t)))
            
        elif t <= t2 + n:
            ves.append(v_max)
            vos.append(lerp(0, v_max, normal_f(120, t3, t)))
            
        elif t<= t3:
            ves.append(lerp(v_max, 0, normal_f(t2 + n, 900, t)))
            vos.append(lerp(0, v_max, normal_f(120, t3, t)))
            
        elif t<= 900:
            ves.append(lerp(v_max, 0, normal_f(t2 + n, 900, t)))
            vos.append(v_max)
            
        elif t<= 960:
            ves.append(0)
            vos.append(lerp(v_max, 0, normal_f(900, 960, t)))

    return ves, vos

def simulate_dangerous_situation(v_func, duration: float):
    
    # 50695
    # 101390 10
    # setting_lists = [[540, 720, 120, 99], [480, 720, 120, 99], [420, 720, 120, 99], [360, 720, 120, 99]]
    setting_lists = [[5 * 60, (22 - 8) * 60, 0, 105.61458]]

    for [t2, t3, n, v_max] in setting_lists:
        
        ves, vos = v_func(t2, t3, n, v_max, duration)
        
        plt.plot([ (ves[i] - vos[i]) for i in range(len(ves)) ])
        plt.show()

        FN = FillSet(features).execute(ves, vos, duration)
        
        print('\n\n========= Dynamic Bearing Capacity Simulation =========\n\n')

        keep_in_sb = 0
        reaching_time = 0
        for t, db in enumerate(FN.dbs):
            if db >= FN.sb:
                
                if keep_in_sb == 0:
                    
                    reaching_time = t
                    
                
                keep_in_sb += 1
                
        
        print('\n\n========= Dangerous Max Velocity Situation =========\n\n')
        print(f'Max velocity = {v_max}\n\n')
        
        print('====== Static Bearing Capacity Reached Time ======\n\n')
        print(f'Reaching Time: {reaching_time}\n\n')
                
        print('\n\n====== Static Bearing Capacity Keeping Time ======\n\n')
        print(keep_in_sb)
                
        print('\n\n====== Velocity of Entrying ======\n\n')
        print(f'{int(ves[reaching_time])} / min')
                
        print('\n\n====== Velocity of Exiting ======\n\n')
        print(f'{int(vos[reaching_time])} / min')
        
        print('\n\n====== Dynamic Bearing Capacity Simulation ======\n\n')
        print([int(db) for db in FN.dbs])
        
        FN.show_plot()

if __name__ == '__main__':
    # Read shapefiles and parse line or polygon features
    features = prepare_features([[config.DIR_RESOURCE_LINE, 'Line'], [config.DIR_RESOURCE_POLYGON, 'Polygon']])
    simulation_duration = 16 * 60  # From 8:00 AM to 24:00 PM

    simulate_dangerous_situation(simulate_seperate_ve_vo, simulation_duration)
