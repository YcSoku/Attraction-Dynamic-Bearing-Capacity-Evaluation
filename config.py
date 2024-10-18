import os

DIR_ROOT                        =   os.path.dirname(os.path.abspath(__file__))
DIR_RESOURCE                    =   os.path.join(DIR_ROOT, 'Data')
DIR_RESOURCE_LINE               =   os.path.join(DIR_RESOURCE, 'All_Line.shp')
DIR_RESOURCE_POLYGON            =   os.path.join(DIR_RESOURCE, 'All_polygon.shp')

FEATURE_ATTRIBUTE_ID            =   'ID'

LINE_ATTRIBUTE_CLASS            =   'class'
LINE_ATTRIBUTE_WAIT_TIME        =   '停留时间'
LINE_ATTRIBUTE_CAPACITY         =   'Capacity'
LINE_ATTRIBUTE_BIDIRECTIONAL    =   'Bidirectio'

POLYGON_ATTRIBUTE_AREA          =   'Area'
POLYGON_ATTRIBUTE_NAME          =   'Name'
POLYGON_ATTRIBUTE_CLASS         =   '分区'
POLYGON_ATTRIBUTE_REMARK        =   '备注信息'
POLYGON_ATTRIBUTE_CAPACITY      =   'Capacity'
POLYGON_ATTRIBUTE_WAIT_TIME     =   '通行时间1'
POLYGON_GATEWAY_NAME            =   ['人行出入口', '车行出入口']

TIME_STEP_MINUTE                =   1

PRINT_FILTERED_FEATURE_INFO     =   False