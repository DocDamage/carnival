"""Prepare explicit unaccepted corridor guides from the existing 1 m floor survey.

The older survey stored connected-component nodes but not accepted edge pairs.
These are candidate paths only: the gameplay pawn must validate every segment.
"""
import collections,hashlib,json,math
from pathlib import Path
from industrial_hospital_route_config import HOSPITAL_YAW,hospital_level_transform
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Saved/IndustrialHospital/Hospital_Room_Connectivity.json'
data=json.loads(source.read_text())
if not data.get('success') or data.get('entrance_component') is None: raise RuntimeError('No successful hospital floor survey')
nodes={tuple(p) for p in data['components'][data['entrance_component']]['nodes']}
start=tuple(data['entrance_seed']); step=data['step_cm']
queue=collections.deque([start]); previous={start:None}
while queue:
    p=queue.popleft()
    for dx,dy in ((step,0),(-step,0),(0,step),(0,-step)):
        q=(p[0]+dx,p[1]+dy)
        if q in nodes and q not in previous: previous[q]=p; queue.append(q)
targets={
    'hospital_corridor_west':min(previous,key=lambda p:(p[0],abs(p[1]-start[1]))),
    'hospital_corridor_east':max(previous,key=lambda p:(p[0],-abs(p[1]-start[1]))),
    'hospital_corridor_south':min(previous,key=lambda p:(p[1],abs(p[0]-start[0]))),
}
origin=hospital_level_transform(); a=math.radians(HOSPITAL_YAW)
report={'accepted':False,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_floor_nodes':data['free_nodes'],'entrance_component_nodes':len(nodes),'component_count':len(data['components']),
        'limits':'Candidate grid adjacency; source omitted individual blocked-edge coordinates. Requires actual pawn collision/return/camera test. Only entrance-connected ground-floor region covered.',
        'routes':{}}
for name,target in targets.items():
    path=[]; p=target
    while p is not None: path.append(p); p=previous[p]
    path.reverse(); simplified=[path[0]]
    for i in range(1,len(path)-1):
        before=(path[i][0]-path[i-1][0],path[i][1]-path[i-1][1]); after=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1])
        if before!=after: simplified.append(path[i])
    simplified.append(path[-1])
    points=[(origin[0]+x*math.cos(a)-y*math.sin(a),origin[1]+x*math.sin(a)+y*math.cos(a),origin[2]+data['sampled_floor_z']) for x,y in simplified]
    report['routes'][name]={'target_local_cm':target,'candidate_floor_points_cm':points,'grid_node_count':len(path),'length_m':(len(path)-1)*step/100}
out=ROOT/'Saved/IndustrialHospital/Hospital_Candidate_Routes.json'; out.write_text(json.dumps(report,indent=2))
print(json.dumps({'file':str(out),'accepted':False,'routes':{n:{'length_m':r['length_m'],'waypoints':len(r['candidate_floor_points_cm'])} for n,r in report['routes'].items()}},indent=2))
