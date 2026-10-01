"""Stop players falling through upper-floor holes into hospital spaces they cannot leave.

The hospital_fine audit (hospital_fine_holes_20261001) lists every move from returnable floor that drops into a
trap. For each, the hole beside the upper floor cell is mapped on a 25 cm grid (no floor within 60 cm below
the upper floor level), and an invisible slab (InvisibleWall collision: blocks pawns, ignores visibility and
camera) is laid flush with the upper floor over it. The hole stays visible. Saves only the hospital set-dress
level (backed up); the persistent map hash is checked unchanged."""
import collections,hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
LEVEL='L_IndustrialHospitalSetDress';LEVEL_FILE=ROOT/('Content/Carnival/World/Levels/'+LEVEL+'.umap')
AUDIT=ROOT/'Saved/WorldExpansion/Reachability/hospital_fine_holes_20261001/index.json'
OUT=ROOT/'Saved/WorldExpansion/HospitalHoleGuards_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;G=25.0
R={'success':False,'errors':[],'guards':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_hole_guards.umap'));R['map_sha256_before']=sha(MAPFILE)
 entries=json.loads(AUDIT.read_text())['trap_entries']
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert not [a for a in EA.get_all_level_actors() if a.get_actor_label().startswith('Hospital_HoleGuard')]
 def floor_at(x,y,z):
  h=unreal.SystemLibrary.line_trace_single(w,V(x,y,z+40),V(x,y,z-60),TQ,False,[],N,True)
  t=h.to_tuple() if h else None
  return bool(t and t[0])
 holes={}
 for a,b in entries:
  z=a[2];key=None
  # Start in the gap just past the upper cell, toward the fall.
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy) or 1
  for s in (30,50,75,100):
   sx,sy=a[0]+dx/L*s,a[1]+dy/L*s
   if not floor_at(sx,sy,z):key=(round(sx/G),round(sy/G),round(z));break
  if not key:continue
  holes.setdefault(round(z),set())
  # Flood the hole (no floor) within 4 m of the entry.
  q=collections.deque([key[:2]]);seen={key[:2]};cells=[]
  while q:
   ix,iy=q.popleft();x,y=ix*G,iy*G
   if math.hypot(x-a[0],y-a[1])>400 or floor_at(x,y,z):continue
   cells.append((ix,iy))
   for ddx,ddy in ((1,0),(-1,0),(0,1),(0,-1)):
    n=(ix+ddx,iy+ddy)
    if n not in seen:seen.add(n);q.append(n)
  holes[round(z)].update(cells)
 # Group hole cells per level into connected patches and guard each with a slab over its bounding box.
 assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name(LEVEL)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube');k=0
 for z,cells in holes.items():
  cells=set(cells)
  while cells:
   s=cells.pop();comp=[s];q=collections.deque([s])
   while q:
    c=q.popleft()
    for ddx,ddy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
     n=(c[0]+ddx,c[1]+ddy)
     if n in cells:cells.discard(n);comp.append(n);q.append(n)
   xs=[c[0]*G for c in comp];ys=[c[1]*G for c in comp]
   x0,x1,y0,y1=min(xs)-G,max(xs)+G,min(ys)-G,max(ys)+G
   g=EA.spawn_actor_from_class(unreal.StaticMeshActor,V((x0+x1)/2,(y0+y1)/2,z-10),unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
   assert '/'+LEVEL+'.' in g.get_path_name()
   g.set_actor_label('Hospital_HoleGuard_%02d'%k);k+=1
   c=g.static_mesh_component;c.set_static_mesh(cube);c.set_collision_profile_name('InvisibleWall')
   c.set_editor_property('cast_shadow',False);g.set_actor_hidden_in_game(True)
   g.set_actor_scale3d(V((x1-x0)/100,(y1-y0)/100,0.2))
   R['guards'].append({'label':g.get_actor_label(),'z_top':z,'x':[round(x0),round(x1)],'y':[round(y0),round(y1)],'hole_cells':len(comp)})
 assert unreal.EditorLoadingAndSavingUtils.save_packages([unreal.EditorLevelLibrary.get_editor_world().get_outermost()] if False else [next(a for a in EA.get_all_level_actors() if '/'+LEVEL+'.' in a.get_path_name()).get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
