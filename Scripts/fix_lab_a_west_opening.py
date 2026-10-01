"""Open the Lab A west connector to Lab B.

The authored west opening (removed SM_MWall03-700x350-8) still had BP_LabCapsule11_1 standing
in it, and Lab A's raised platform (651) sits 50 cm above Lab B's corridor (601), beyond a
character's 45 cm step. This removes that capsule prop and mirrors Lab A's own interior step
group (two Steps-50 pieces, their stair overlays and side pieces) onto the opening, rising from
Lab B's corridor onto the platform. Only the Lab A level is saved (backed up first).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
LEVEL='L_CarnivalWorldExpansion_LabA'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
A=(-42097.962876199206,-7043.716818882417,600.0);YAW=-57.0
OUT=ROOT/'Saved/WorldExpansion/LabAWestOpeningFix_20260930';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[],'removed':[],'spawned':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def to_world(lx,ly,lz):
 c,s=math.cos(math.radians(YAW)),math.sin(math.radians(YAW))
 return unreal.Vector(A[0]+c*lx-s*ly,A[1]+s*lx+c*ly,A[2]+lz)
def to_local(v):
 x,y=v.x-A[0],v.y-A[1];c,s=math.cos(math.radians(-YAW)),math.sin(math.radians(-YAW))
 return (c*x-s*y,s*x+c*y,v.z-A[2])
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE))
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_west_opening.umap'))
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 mine=[a for a in EA.get_all_level_actors() if '/'+LEVEL+'.'+LEVEL+':' in a.get_path_name()]
 assert not any(a.get_actor_label().startswith('LabWestConnector_') for a in mine),'Already repaired'
 assert LE.set_current_level_by_name(LEVEL)
 caps=[a for a in mine if a.get_actor_label()=='BP_LabCapsule11_1'];assert len(caps)==1
 l=to_local(caps[0].get_actor_location());assert abs(l[0]+1421)<5 and abs(l[1]-400)<5,'Unexpected capsule position'
 R['removed'].append({'label':'BP_LabCapsule11_1','class':caps[0].get_class().get_name(),'local':l,'reason':'stood in the authored west opening'})
 EA.destroy_actor(caps[0])
 group=[a for a in mine if a.get_actor_label().startswith(('SM_MFloor02-Steps-50','SM_MFloor02-StepsSide-50','SM_MStair01-Steps-350x50'))]
 assert len(group)==6
 for src in group:
  lx,ly,lz=to_local(src.get_actor_location())
  # 180-degree turn about the source group's centre (-375,400), moved to the west edge (-1423,400).
  nx,ny=-1798.0-lx,800.0-ly
  r=src.get_actor_rotation()
  a=EA.spawn_actor_from_class(unreal.StaticMeshActor,to_world(nx,ny,lz),unreal.Rotator(roll=r.roll,pitch=r.pitch,yaw=r.yaw+180.0))
  a.static_mesh_component.set_static_mesh(src.static_mesh_component.static_mesh)
  a.set_actor_scale3d(src.get_actor_scale3d())
  a.static_mesh_component.set_collision_profile_name(src.static_mesh_component.get_collision_profile_name())
  mats=src.static_mesh_component.get_materials()
  for i,m in enumerate(mats):a.static_mesh_component.set_material(i,m)
  label='LabWestConnector_'+src.get_actor_label();a.set_actor_label(label);a.set_folder_path('WestConnector')
  assert '/'+LEVEL+'.' in a.get_path_name()
  R['spawned'].append({'label':label,'source':src.get_actor_label(),'local':[nx,ny,lz],'yaw_world':r.yaw+180.0})
 level=caps[0] if False else next(x for x in EA.get_all_level_actors() if x.get_actor_label()==R['spawned'][0]['label']).get_outermost()
 assert unreal.EditorLoadingAndSavingUtils.save_packages([level],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE))
 assert R['map_sha256_after']==R['map_sha256_before'],'Root map changed'
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
