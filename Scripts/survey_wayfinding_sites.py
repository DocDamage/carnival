"""Read-only survey of supported sign verges, including invisible-wall collision."""
import json,math,os,sys,traceback
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from wayfinding_layout import ROOT,SITES,TAG
OUT=ROOT/('Saved/WorldExpansion/'+os.environ.get('CARNIVAL_WAYFINDING_SURVEY','WayfindingSurvey_20261029_v4')+'.json')
V=unreal.Vector;OT=[unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
R={'success':False,'errors':[],'sites':[]}
paths=[]
for source in ('WorldExpansion/Walk_Route_Playtest_CappedEdges_20261029.json','IndustrialHospital/Route_Playtest_After_PropResite_20261001.json'):
 for test in json.loads((ROOT/'Saved'/source).read_text())['tests']:
  if source.startswith('Industrial') and not test['name'].startswith('walk'):continue
  points=[s.get('position_cm',s.get('position')) for s in test['samples']]
  paths.extend(zip(points,points[1:]))
def route_clearance(p):
 distances=[]
 for a,b in paths:
  dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
  if den<1:continue
  t=max(0,min(1,((p.x-a[0])*dx+(p.y-a[1])*dy)/den))
  z=a[2]+t*(b[2]-a[2])-98.15
  if abs(p.z-z)<200:distances.append(math.hypot(p.x-a[0]-t*dx,p.y-a[1]-t*dy))
 return min(distances,default=99999)
def hit(h):
 d=h.to_tuple() if h else None
 return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ignore=[a for a in actors if a.get_actor_label().startswith('SM_Landscape_Far_01a') or isinstance(a,unreal.PhysicsVolume) or TAG in [str(t) for t in a.tags]]
 caps=[a for a in actors if 'CarnivalEdgeFenceCap' in [str(t) for t in a.tags]]
 for key,center,yaw,offset,front,back in SITES:
  a=math.radians(yaw);forward=V(math.cos(a),math.sin(a),0);side=V(-math.sin(a),math.cos(a),0)
  rec={'id':key,'center':center,'yaw':yaw,'front':front,'back':back,'rejected':[]};chosen=None
  for along in (0,-300,300,-600,600,-900,900):
   for sign in (-1,1):
    p=V(*center)+forward*along+side*(offset*sign)
    h=hit(unreal.SystemLibrary.line_trace_single(world,p+V(0,0,180),p-V(0,0,400),unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignore,unreal.DrawDebugTrace.NONE,True))
    if not h or h[7].z<.7:
     rec['rejected'].append({'at':p.to_tuple(),'reason':'unsupported'});continue
    base=V(p.x,p.y,h[5].z)
    clearance=route_clearance(base)
    if clearance<(140 if key in ('ResearchLab','SewerStairs') else 270):
     rec['rejected'].append({'at':base.to_tuple(),'reason':'too close to tested route','clearance_cm':clearance});continue
    post=hit(unreal.SystemLibrary.capsule_trace_single_for_objects(world,base+V(0,0,235),base+V(0,0,236),24,225,OT,False,ignore,unreal.DrawDebugTrace.NONE,True))
    if post:
     rec['rejected'].append({'at':base.to_tuple(),'reason':'post blocked','actor':post[9].get_actor_label() if post[9] else None});continue
    board=hit(unreal.SystemLibrary.box_trace_single_for_objects(world,base+V(0,0,355),base+V(0,0,356),V(12,166,73),unreal.Rotator(yaw=yaw),OT,False,ignore+caps,unreal.DrawDebugTrace.NONE,True))
    if board:
     rec['rejected'].append({'at':base.to_tuple(),'reason':'board occluded','actor':board[9].get_actor_label() if board[9] else None});continue
    chosen=base;rec.update(base=base.to_tuple(),support=h[9].get_path_name() if h[9] else None,along=along,side=sign,route_clearance_cm=clearance)
    break
   if chosen:break
  if not chosen:R['errors'].append('No sign verge at '+key)
  R['sites'].append(rec)
 R['assets']={p:bool(unreal.load_asset(p)) for p in ('/Engine/BasicShapes/Cube','/Engine/EngineFonts/RobotoDistanceField','/Engine/EngineMaterials/DefaultTextMaterialOpaque')}
 assert all(R['assets'].values()),R['assets']
 R['success']=not R['errors']
except Exception:R['errors'].append(traceback.format_exc());raise
finally:OUT.write_text(json.dumps(R,indent=2))
