"""Connect the dock pieces that could not be reached:
 - North Dock: NorthDock_End_Platform (top 645) was 10.75 m north of NorthDock_Bent_Quay (top 635).
 - East Dock: the three EastDock_Loading_Finger decks (top 660) started 33.5 m north of EastDock_Main_Quay (645).
Each link is a 4 m deck slab using the dock's own deck mesh and materials, graded flush from one deck top to
the other (overlapping 10 cm into each), with copies of the dock's own piles underneath where the dock has
them. Saves only the two dock levels (backed up); the persistent map hash is checked unchanged."""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LV=ROOT/'Content/Carnival/World/Levels'
NORTH='L_CarnivalWorldExpansion_DocksNorth_Layout';EAST='L_CarnivalWorldExpansion_DocksEast'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/DockPieceLinks_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;W=400.0;OVER=10.0
# (level, source deck label, link label, x, y_from, top_from, y_to, top_to)
LINKS=[(NORTH,'NorthDock_Bent_Quay','NorthDock_EndPlatform_Link',-55400.0,-47350.0,635.0,-46275.0,645.0),
 (EAST,'EastDock_Main_Quay','EastDock_Finger_Link_West',67300.0,18850.0,645.0,22200.0,660.0),
 (EAST,'EastDock_Main_Quay','EastDock_Finger_Link_Centre',70000.0,18850.0,645.0,22200.0,660.0),
 (EAST,'EastDock_Main_Quay','EastDock_Finger_Link_East',72700.0,18850.0,645.0,22200.0,660.0)]
R={'success':False,'errors':[],'links':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R['map_sha256_before']=sha(MAPFILE)
 for n in (NORTH,EAST):shutil.copy2(LV/(n+'.umap'),OUT/(n+'.before_links.umap'))
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors();by={a.get_actor_label():a for a in acts}
 for lv,src,label,x,y0,t0,y1,t1 in LINKS:
  assert label not in by,label+' exists'
  s=by[src];sc=s.static_mesh_component;mesh=sc.static_mesh
  mats=[sc.get_material(i) for i in range(sc.get_num_materials())]
  so,se=s.get_actor_bounds(False);thick=se.z*2
  mb=mesh.get_bounds();mext=mb.box_extent
  assert LE.set_current_level_by_name(lv)
  ya,yb=y0-OVER,y1+OVER;L=yb-ya;rise=t1-t0;pitch=math.degrees(math.atan2(rise,(y1-y0)))
  a=EA.spawn_actor_from_class(unreal.StaticMeshActor,V(x,(ya+yb)/2,0),unreal.Rotator(roll=0.0,pitch=pitch,yaw=90.0))
  assert '/'+lv+'.' in a.get_path_name(),a.get_path_name()
  a.set_actor_label(label);c=a.static_mesh_component;c.set_static_mesh(mesh)
  for i,m in enumerate(mats):c.set_material(i,m)
  c.set_collision_profile_name(sc.get_collision_profile_name())
  a.set_actor_scale3d(V(L/(mext.x*2),W/(mext.y*2),thick/(mext.z*2)))
  # Put the slab's top centre at the mid-height of the two deck tops.
  o,e=a.get_actor_bounds(False);want_top=(t0+t1)/2
  a.set_actor_location(a.get_actor_location()+V(x-o.x,(ya+yb)/2-o.y,want_top-(o.z+e.z)+ (L/2)*math.sin(math.radians(abs(pitch)))),False,True)
  o,e=a.get_actor_bounds(False)
  # Measured tops at both ends of the link.
  ends=[]
  for yy in (y0+20,y1-20):
   h=unreal.SystemLibrary.line_trace_single(w,V(x,yy,2000),V(x,yy,-500),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
   t=h.to_tuple() if h else None;ends.append(round(t[5].z,1) if t and t[0] else None)
  rec={'label':label,'level':lv,'pitch':round(pitch,3),'length_cm':round(L),'end_tops':ends,'want':[t0,t1],'piles':[]}
  piles=[p for p in acts if 'Pile' in p.get_actor_label() and '/'+lv+'.' in p.get_path_name() and isinstance(p,unreal.StaticMeshActor)]
  if piles:
   pile=piles[0];po,pe=pile.get_actor_bounds(False);deck_bottom=min(t0,t1)-thick
   for yy in (y0+L*0.35,y0+L*0.7):
    for side in (-1,1):
     loc=pile.get_actor_location();pc=pile.static_mesh_component
     d=EA.spawn_actor_from_class(unreal.StaticMeshActor,V(x+side*(W/2-40),yy,loc.z+(deck_bottom-(po.z+pe.z))),pile.get_actor_rotation())
     d.set_actor_label(label+'_Pile');dc=d.static_mesh_component;dc.set_static_mesh(pc.static_mesh)
     for i in range(pc.get_num_materials()):dc.set_material(i,pc.get_material(i))
     d.set_actor_scale3d(pile.get_actor_scale3d())
     rec['piles'].append([round(v) for v in d.get_actor_location().to_tuple()])
  R['links'].append(rec)
 pk=[]
 for n in (NORTH,EAST):
  x=next(a for a in EA.get_all_level_actors() if '/'+n+'.' in a.get_path_name());pk.append(x.get_outermost())
 assert unreal.EditorLoadingAndSavingUtils.save_packages(pk,False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
