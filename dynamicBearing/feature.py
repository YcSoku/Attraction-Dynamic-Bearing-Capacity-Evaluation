import config
from osgeo import ogr

def create_instance(class_name, *args, **kwargs):
    
    return globals()[class_name](*args, **kwargs)

class Feature:
    
    def __init__(self, feature):
        
        self.sb = 0  # sbc = Static Bearing Capacity
        self.connected_features = {}
        self.geometry_type = 'UNKNOWN'
        self.properties = feature.items()
        self.geometry = feature.GetGeometryRef().Clone()
        self.id = self.properties[config.FEATURE_ATTRIBUTE_ID]
    
    def intersect(self, id: str):
        return id in self.connected_features
    
    def get_all_connected_features(self):
        
        connected_feature_dict = {}
        stack: list[Feature] = [self]
        
        while stack:
            feature = stack.pop()
            connected_feature_dict[feature.id] = feature
            for _feature in feature.connected_features.values():
                if _feature.id not in connected_feature_dict:
                    stack.append(_feature)
        
        return connected_feature_dict.values()
    
    def check_nested_isolation(self):
        
        # True if isolation
        if len(self.connected_features) == 0:
            return True
        
        # Check a only intersects b and b only intersects a
        if len(self.connected_features) == 1:
            key = next(iter(self.connected_features))
            feature: Feature = self.connected_features[key]
            
            return True if len(feature.connected_features) == 1 and self.id in feature.connected_features else False
        
        return False

class Line(Feature):
    
    def __init__(self, feature):
        super().__init__(feature)
        
        self.geometry_type = 'LINE'
        self.sb = self.properties[config.LINE_ATTRIBUTE_CAPACITY]  # sbc = Static Bearing Capacity
        self.class_type = self.properties[config.LINE_ATTRIBUTE_CLASS]
        self.wait_time = self.properties[config.LINE_ATTRIBUTE_WAIT_TIME]
        self.bidirectional = bool(self.properties[config.LINE_ATTRIBUTE_BIDIRECTIONAL])

class Polygon(Feature):
    
    def __init__(self, feature):
        super().__init__(feature)
        
        self.geometry_type = 'POLYGON'
        self.area = self.properties[config.POLYGON_ATTRIBUTE_AREA]
        self.name = self.properties[config.POLYGON_ATTRIBUTE_NAME]
        self.sb = self.properties[config.POLYGON_ATTRIBUTE_CAPACITY]  # sbc = Static Bearing Capacity
        self.remark = self.properties[config.POLYGON_ATTRIBUTE_REMARK]
        self.class_type = self.properties[config.POLYGON_ATTRIBUTE_CLASS]
        self.wait_time = self.properties[config.POLYGON_ATTRIBUTE_WAIT_TIME]
    
    def is_entrance(self):
        
        return self.name in config.POLYGON_GATEWAY_NAME
    
def check_connectivity(feature: Feature, features: list[Feature]):
    
    for _feature in features:
        
        if _feature.id != feature.id and not feature.intersect(_feature.id) and check_intersect(_feature, feature):
            
            feature.connected_features[_feature.id] = _feature
            _feature.connected_features[feature.id] = feature

def check_intersect(feature_a: Feature, feature_b: Feature):
    
    do_intersect = feature_a.geometry.Intersects(feature_b.geometry)
    do_touch = feature_a.geometry.Touches(feature_b.geometry)
    return do_intersect or do_touch
        
def prepare_features(path_descs: list[list[str, str]]) -> list[Feature]:
    
    # Process 1: Initialization
    features: list[Feature] = []
    
    for [path, class_name] in path_descs:
        shp = ogr.Open(path)
        layer = shp.GetLayer()
    
        for feature in layer:
            features.append(create_instance(class_name, feature))
            
        layer = None
        shp = None
    
    for feature in features:
        check_connectivity(feature, features)
    
    # Process 2: Validation
    entrances: list[Feature] = []
    for feature in features:
        if feature.geometry_type == "POLYGON" and feature.is_entrance() and not feature.check_nested_isolation():
            entrances.append(feature)
    
    connected_feature_dict = {}
    for entrance in entrances:
        for feature in entrance.get_all_connected_features():
            connected_feature_dict[feature.id] = feature
    
    connected_features = connected_feature_dict.values()
    
    if config.PRINT_FILTERED_FEATURE_INFO:
        c_dict: dict[Feature] = {}
        for feature in connected_features:
            c_dict[feature.id] = feature
            
        for feature in features:
            if feature.id not in c_dict:
                print(feature.id, feature.geometry_type, feature.connected_features.keys())
    
    return list(connected_features)
