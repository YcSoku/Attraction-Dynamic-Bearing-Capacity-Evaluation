import math
import config
import matplotlib.pyplot as plt
from dbc.feature import Feature

class FillNode:
    
    def __init__(self, feature: Feature):
        
        self.ts = []            # Input time: time list recording time values when this node is filled
        self.vs = []            # Input velocity: velocity list recording velocity values at which this node is filled at a specific time point within self.ts
        self.tf = None          # Time of filling: the time when this node finished filling (before it is filled, self.tf is None always)
        self.feature = feature
        self.sb = feature.sb
        self.db = 0.0           # Dynamic Bearing Capacity

class FillQueue:
    
    def __init__(self):
        
        self.queue: list[FillNode] = []
    
    def add(self, node: FillNode):
        
        self.queue.append(node)

    def has_node(self, id: str):
        
        for node in self.queue:
            if node.feature.id == id:
                return True
        return False
        
class FillSet:
    
    def __init__(self, features: list[Feature]):
        
        self.simulation_duration = 0.0
        self.total_passenger_flow = 0
        self.fns: list[FillNode] = []
        self.features = features
        self.current_time = 0.0
        self.unique_set = set()
        self.FQ = FillQueue()
        self.dbs = []
        self.sb = 0.0
        
        for feature in features:
            self.sb += feature.sb
        
        # Add entrances to FQ
        for feature in features:
            if feature.geometry_type == 'POLYGON' and feature.is_entrance():
                node = FillNode(feature)
                node.sb = 0.0
                node.db = 0.0
                node.tf = 0.0
                self.FQ.add(node)
        
        self._initialize()
    
    def add(self, feature: Feature):
        
        # New node must have not yet existed in fill set or fill queue
        if not feature.id in self.unique_set and not self.FQ.has_node(feature.id):
        
            node = FillNode(feature)
            self.fns.append(node)
            self.unique_set.add(feature.id)
            
    def remove(self, id):
        
        if id not in self.unique_set:
            return None
        
        self.unique_set.remove(id)
        
        index = 0
        for fn in self.fns:
            if fn.feature.id == id:
                break
            index += 1
        node = self.fns.pop(index)
        
        return node
    
    # Step 1
    def _initialize(self):
        
        for feature in self.features:
            if feature.geometry_type == 'POLYGON' and feature.is_entrance():
                
                for id in feature.connected_features:
                    
                    _feature = feature.connected_features[id]
                    
                    # Add adjacent road (near the entrence) to fns
                    if _feature.sb == 0.0 and _feature.id not in self.unique_set:
                        node = FillNode(_feature)
                        if self.FQ.has_node(node):
                            continue
                        node.tf = 0.0
                        self.fns.append(node)
                        self.unique_set.add(node.feature.id)
                        
        return self
    
    # Pick filled node having the minimun tf in self.fns
    def pick_filled_node(self):
        
        min_tf_node = None
        min_tf = float('inf')
        
        # Find a node has tf (is completed)
        for fn in [_fn for _fn in self.fns if _fn.tf is not None]:
            if fn.tf < min_tf:
                min_tf = fn.tf
                min_tf_node = fn
                
        return min_tf_node

    # Pick filling node having the minumum remaining capacity (sb - db) in self.fns
    def pick_filling_node(self):
        
        min_remaining_node = None
        min_remaining_capacity = float('inf')
        
        for fn in self.fns:
            remaining_capacity = fn.sb - fn.db
            if remaining_capacity < min_remaining_capacity:
                min_remaining_node = fn
                min_remaining_capacity = remaining_capacity
        
        return min_remaining_node
            
    
    def update_FQ(self):
        
        # Step 2 pick a filled node and transfer it to FQ
        min_tf_node = self.pick_filled_node()
        if min_tf_node is not None:
            min_tf_node.ts.append(min_tf_node.tf)
            self.FQ.add(min_tf_node)
            
            # Step 3
            self.remove(min_tf_node.feature.id)
            
            for id in min_tf_node.feature.connected_features:
                feature = min_tf_node.feature.connected_features[id]
                self.add(feature) # Step 4
    
    def tick(self, t: float, v: float, time_step: float):
        
        self.update_FQ()
        if len(self.fns) == 0:
            return 0.0
        
        # Step 5
        filling_node = self.pick_filling_node()
        filling_time = (filling_node.sb - filling_node.db) / v
        
        # Filling
        filling_node.ts.append(t)
        filling_node.vs.append(v)
        
        # Can be filled in this time_step => update tf
        if filling_time <= time_step:
            filling_node.tf = t + filling_time
            filling_node.db = filling_node.sb
            
            return time_step - filling_time
        
        # Cannot be filled
        filling_node.db += time_step * v
        return 0
        
    # Step 6
    def execute(self, vs, duration):
        
        for v in vs:
            if v > 0:
                self.total_passenger_flow += v
        
        self.simulation_duration = duration
        time_step = config.TIME_STEP_MINUTE
        
        # Simulation Loop
        while self.current_time < duration:
            
            v = vs[int(self.current_time)]
            
            if v > 0:
                
                # Tick
                time_left = self.tick(self.current_time, v, time_step)

                if time_left != 0.0:
                    time_step = time_left  
                    self.current_time = math.floor(self.current_time) + 1.0 - time_step
                else:
                    time_step = config.TIME_STEP_MINUTE
                    self.current_time = math.floor(self.current_time) + 1.0
                    
            else: # v <= 0
                
                # TODO: Too weak! Error will happen if v[i] <= 0 and then v[i+1] > 0
                time_step = config.TIME_STEP_MINUTE
                self.current_time = math.floor(self.current_time) + 1.0
            
        # After simulation loop
        # Add filling node (if existed in self.fns) to FQ
        if len(self.fns) != 0:
            filling_node = self.pick_filling_node()
            filling_node.tf = self.current_time
            filling_node.ts.append(filling_node.tf)
            self.FQ.add(filling_node)
            
        self.record_db(vs)
        return self
    
    def calculate_db(self, t: float):
        
        db = 0
        for fn in self.FQ.queue:
            
            if t >= fn.tf:
                db += fn.sb
                
            else: 
                # Find last j where t > fn.ts[j]
                for j in range(len(fn.ts)):
                    if t < fn.ts[j]:
                        j -= 1
                        break
                
                # Sum all sub-dbs before time j
                for k in range(j): db += fn.vs[k] * (fn.ts[k + 1] - fn.ts[k])
                
                # Add the interpolated result between time j and time j + 1
                db += fn.vs[j] * (t - fn.ts[j]) / (fn.ts[j + 1] - fn.ts[j])
                break
            
        return db
    
    def record_db(self, vs: list[float]):
        
        for t, v in enumerate(vs):
            
            if v > 0:
                db = self.calculate_db(t)
            else:
                db = 0 if len(self.dbs) == 0 else max(int(self.dbs[-1] + v), 0)
                
            self.dbs.append(db)
        
    def get_not_filled_features(self):
        
        r_set = set()
        for node in self.FQ.queue:
            r_set.add(node.feature.id)
        
        nf_features: list[Feature] = []
        for feature in self.features:
            if feature.id not in r_set:
                nf_features.append(feature)
        return nf_features
    
    def show_result(self, visualization: bool = True):
        
        print('\n\n========= Attraction Dynamic Bearing Capacity Simulation  =========\n\n')
        print(f'The Static Bearing Capacity is {self.sb}\n\n')
        
        print('====== Simulated Total Passenger Flow  ======\n\n')
        print(f'{int(self.total_passenger_flow)}\n\n')
        
        print('====== Dynamic Bearing Capacity  ======\n\n')
        print([int(db) for db in self.dbs])
        
        # Check not filled feature
        no_filled_feature = self.get_not_filled_features()
        
        if len(no_filled_feature) != 0:
            print('\n\nThe attraction not reached its max static bearing capacity.\n\n')
            print('====== No Filled Features ======\n\n')
            
        for feature in no_filled_feature:
            print(feature.id, feature.geometry_type, feature.connected_features.keys())
            
        if visualization:
            self.show_plot()
        
    def show_plot(self):
        
        plt.plot(self.dbs)
        
        plt.title('Dynamic Carrying Capacity of Attraction')
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Dynamic Bearing Capacity (number of people)')
        
        plt.show()
