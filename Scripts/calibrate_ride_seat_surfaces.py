"""Derive initial passenger anchors from reviewed exported mesh triangles.

The locations below select visible bench/basket surfaces, not arbitrary actor
origins. The resulting manifest records the intersected triangle and normal.
Animation fit, restraints, and moving camera clearance require runtime review.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/RideDevelopment/SeatGeometry'
source = json.loads((OUT/'index.json').read_text())
requests = {
    'SM_BalloonRide_seat_01a': {'standing': True, 'points': [(0,0,0,0)], 'note': 'Standing basket floor; one passenger per basket'},
    'SM_ClownRideseat': {'points': [(-65,0,16,0),(0,65,16,-90),(0,-65,16,90)], 'note': 'Three inward facing perimeter bench positions; gate at +X stays open'},
    'SM_vehicle_01a': {'points': [(50,-40,12,90)], 'note': 'One centered passenger on the actual Flying Bobs seat cushion'},
    'SM_Teapot_Ride_Cup': {'points': [(65,0,70,180),(-65,0,70,0)], 'note': 'Two opposed inward-facing bench positions clear of wheel and doorway'},
    'SM_Cabin_01a': {'points': [(x,y,-255,180 if x>0 else 0) for x in (-100,100) for y in (-55,55)], 'note': 'Four inward-facing bench positions below the cabin roof'},
    'SM_CarousalBench_01a': {'points': [(x,y,70,0 if x>0 else 180) for x in (-60,60) for y in (-30,30)], 'note': 'Four back-to-back bench passengers; horses require a separate straddle animation'},
    'SM_Hotair_Balloon': {'standing': True, 'points': [(x,y,-646,0) for x in (-70,70) for y in (-70,70)], 'note': 'Four standing positions on the actual basket floor'},
    'SM_Mainboat_PirateRide': {'points': [(x,y,z,0 if x<0 else 180) for x,z in [(-500,-965),(-400,-984),(-300,-998),(-200,-1009),(-100,-1014),(100,-1014),(200,-1006),(300,-995),(400,-981),(550,-961)] for y in (-70,70)], 'note': 'Twenty bench positions face the center; support is sampled per row along curved deck'},
}
report = {'schema': 1, 'status': 'measured_initial_authoring_runtime_review_pending',
          'geometry_source': 'Saved/RideDevelopment/SeatGeometry/index.json',
          'source_assets_modified': False, 'meshes': {}}
for item in source['meshes']:
    name = Path(item['obj']).stem
    if name not in requests: continue
    spec = requests[name]
    vertices, faces = [], []
    for line in Path(item['obj']).read_text().splitlines():
        if line.startswith('v '):
            x,z,y = map(float,line.split()[1:4]); vertices.append((x,y,z))
        elif line.startswith('f '): faces.append([int(n.split('/')[0])-1 for n in line.split()[1:4]])
    tri=np.array(vertices)[np.array(faces)]; a=tri[:,0]; u=tri[:,1]-a; v=tri[:,2]-a
    normal=-np.cross(u,v); normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1.e-9)
    det=u[:,0]*v[:,1]-u[:,1]*v[:,0]; valid=np.abs(det)>1.e-5
    anchors=[]
    for x,y,target,yaw in spec['points']:
        dx=x-a[:,0];dy=y-a[:,1]
        s=(dx*v[:,1]-dy*v[:,0])/np.where(valid,det,1)
        t=(u[:,0]*dy-u[:,1]*dx)/np.where(valid,det,1)
        z=a[:,2]+s*u[:,2]+t*v[:,2]
        hits=np.where(valid&(s>=0)&(t>=0)&(s+t<=1)&(normal[:,2]>.7)&(abs(z-target)<12))[0]
        if not len(hits): raise ValueError(f'No supporting triangle for {name} at {x},{y}, target {target}')
        index=int(hits[np.argmin(abs(z[hits]-target))])
        anchors.append({'location':[x,y,round(float(z[index]),3)],'yaw':yaw,
                        'support_triangle':index,'support_normal':normal[index].round(5).tolist()})
    report['meshes'][item['mesh']]={'geometry_reviewed':True,'standing_passenger':spec.get('standing',False),
        'notes':spec['note'],'geometry_review_image':str(Path('Saved/RideDevelopment/SeatGeometry')/(name+'_surfaces.png')),
        'anchors':anchors,'visual_passenger_acceptance':'pending'}
assert len(report['meshes'])==len(requests)
(ROOT/'Config/RideSeatCalibration.json').write_text(json.dumps(report,indent=2)+'\n')
print({path.split('.')[-1]:len(value['anchors']) for path,value in report['meshes'].items()})
