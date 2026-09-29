"""Walk through the hospital entrance and back with the actual player pawn."""
import math
import runpy
import sys
sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import HOSPITAL_YAW, hospital_level_transform

origin = hospital_level_transform()
angle = math.radians(HOSPITAL_YAW)
controls = [(5200,-2300),(5200,-1000),(5000,-850),(5000,-350),(5200,-200)]
local = []
for a,b in zip(controls,controls[1:]):
    count = math.ceil(math.dist(a,b)/50)
    local.extend((a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count))
local.append(controls[-1])
points = [(origin[0]+x*math.cos(angle)-y*math.sin(angle),
           origin[1]+x*math.sin(angle)+y*math.cos(angle), origin[2]+80) for x,y in local]
runpy.run_path(r"F:\Carnival\Scripts\playtest_industrial_hospital_route.py", init_globals={
    "WORLD_ROUTE_POINTS": points, "WALK_ONLY": True,
    "REPORT_PREFIX": "Hospital_Entrance_Playtest",
})
