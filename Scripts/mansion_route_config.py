"""Shared, centimetre-based layout of the Carnival -> wetlands -> mansion route."""
import json,math
from pathlib import Path
ROOT=Path(r'F:\Carnival')
OUT=ROOT/'Saved/MansionConnection'
BASE='/Game/Carnival/World'
CARNIVAL='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
COAST=BASE+'/Levels/L_CoastalMansionApproach'
MANSION=BASE+'/Levels/L_HauntedMansionConnected'
GATE=(-5727.482,-6311.805,102.0)
COAST_YAW=235.0
COAST_Z=-260.0
a=math.radians(COAST_YAW)
COAST_ORIGIN=(GATE[0]+50000*math.cos(a),GATE[1]+50000*math.sin(a),COAST_Z)
MANSION_LOCAL=(52000.0,-7000.0,760.0)
MANSION_LOCAL_YAW=90.0
def world_point(p):
    return (COAST_ORIGIN[0]+p[0]*math.cos(a)-p[1]*math.sin(a),COAST_ORIGIN[1]+p[0]*math.sin(a)+p[1]*math.cos(a),COAST_ORIGIN[2]+p[2])
def mansion_point(p):
    return (MANSION_LOCAL[0]-p[1],MANSION_LOCAL[1]+p[0],MANSION_LOCAL[2]+p[2])
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def smooth_path(ctrl,step=180.0):
    points=[]
    for i in range(len(ctrl)-1):
        p0,p1,p2,p3=ctrl[max(0,i-1)],ctrl[i],ctrl[i+1],ctrl[min(len(ctrl)-1,i+2)]
        count=max(2,math.ceil(distance(p1,p2)/step))
        for j in range(count):
            t=j/count;t2=t*t;t3=t2*t
            points.append(tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t2+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t3) for k in range(3)))
    points.append(tuple(ctrl[-1]));return points
# Record source rail coordinates here so regeneration does not depend on Saved.
RAIL_WEST=[(-1274.878,-72.423),(-4751.769,-75.426),(-7451.768,-75.428),
    (-11651.768,-75.432),(-17697.927,251.808),(-21282.123,575.06),
    (-26196.333,1191.816),(-28870.404,1624.6)]
RAIL_EAST=[(1240.552,-73.037),(2132.567,-71.922),(2731.54,-85.04),
    (4552.58,-169.332),(7242.306,-404.637),(11426.326,-770.667),
    (17420.961,-1623.589),(20963.348,-2257.976),(25805.109,-3300.662),
    (28431.288,-3964.846)]
WEST=[(-50000,0,362),(-47300,-100,375),(-43200,-1500,430),(-38900,-2400,480),(-34600,-1400,470),(-30800,1050,440),(-28870.404,1624.6,430)]
RAIL=[(p[0],p[1],430) for p in reversed(RAIL_WEST)]
RAIL += [(0,-72.7,430)] + [(p[0],p[1],430) for p in RAIL_EAST]
EAST=[(28431.288,-3964.846,430),(31700,-5000,490),(35100,-6300,560),(38300,-7300,650),(41600,-7400,740),(44200,-7150,825),(46600,-7000,858)]
SECTIONS=[{'name':'Carnival_Wetlands','surface':'gravel','width':460,'points':smooth_path(WEST)},
          {'name':'Railroad_Crossing','surface':'timber','width':280,'points':smooth_path(RAIL)},
          {'name':'Mansion_Wetlands','surface':'gravel','width':460,'points':smooth_path(EAST)}]
DRIVEWAY=[(46600,-7000,858),(48000,-7000,858),(49500,-7000,858),(50500,-7000,858)]
def route_manifest():
    route=[]
    for section in SECTIONS:route.extend(section['points'][:-1])
    route+=DRIVEWAY
    length=sum(distance(x,y) for x,y in zip(route,route[1:]))
    return {'coast_origin':COAST_ORIGIN,'coast_yaw':COAST_YAW,'mansion_local':MANSION_LOCAL,'mansion_world':world_point(MANSION_LOCAL),
        'mansion_yaw':COAST_YAW+MANSION_LOCAL_YAW,'length_m':length/100,'normal_speed_cm_s':450,
        'normal_travel_seconds':length/450,'route_local':route,'route_world':[world_point(p) for p in route],
        'sections':SECTIONS,'driveway':DRIVEWAY}
if __name__=='__main__':
    manifest=route_manifest();(OUT/'Route_Layout.json').write_text(json.dumps(manifest,indent=2))
    print('Route:',round(manifest['length_m']), 'metres;',round(manifest['normal_travel_seconds']), 'seconds at normal movement speed')
