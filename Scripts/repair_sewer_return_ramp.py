"""Keep the public ramp above the measured crossing beam in both directions."""
import datetime,json,math,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'pieces':[],'limits':'Saved two-segment floor transition only; requires fresh candidate and continuous production-pawn return.'}
failure=json.loads((OUT/'InteriorCameraAcceptance/SewerLowerCorridor_VentRaised_20260929.json').read_text())
assert not failure['success']
case=failure['cases'][0];assert case['legs'][0]['success']
assert case['legs'][-1]['blocker']['path'].endswith('.StaticMeshActor_584')
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout'
file=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
backup=OUT/'Backups'/('SewerReturnRamp_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/file.name
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);rows=list(actors.get_all_level_actors())
owned=unreal.Name('CarnivalInteriorHandoffRepair')
first=next(a for a in rows if a.get_actor_label()=='SewerStair_PublicFloorHandoff');assert owned in first.tags
material=first.get_component_by_class(unreal.StaticMeshComponent).get_material(0)
# Actual return contacts the beam face at y=-12309.9, whose upper face is
# z=-1783.05. Keep both ramp segments >=5 cm above it at the joint, avoiding
# reliance on the source decorative beam's character step-up policy.
points=[unreal.Vector(-26940,-12585,-1758),unreal.Vector(-26940,-12310,-1778),unreal.Vector(-26940,-12100,-1850)]
for i,(start,finish) in enumerate(zip(points,points[1:])):
 label='SewerStair_PublicFloorHandoff' if i==0 else 'SewerStair_PublicFloorHandoff_Lower'
 actor=first if i==0 else next((a for a in rows if a.get_actor_label()==label),None)
 assert not actor or owned in actor.tags
 if not actor:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
 actor.modify();actor.set_actor_label(label);actor.set_editor_property('tags',[owned])
 comp=actor.get_component_by_class(unreal.StaticMeshComponent);comp.modify()
 comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));comp.set_mobility(unreal.ComponentMobility.STATIC)
 comp.set_collision_profile_name('BlockAll')
 if material:comp.set_material(0,material)
 delta=finish-start;pitch=math.degrees(math.atan2(delta.z,math.hypot(delta.x,delta.y)));assert abs(pitch)<20
 thickness=25;center=(start+finish)*.5-unreal.Vector(0,0,thickness*.5*math.cos(math.radians(pitch)))
 actor.set_actor_location(center,False,True);actor.set_actor_rotation(unreal.Rotator(pitch=pitch,yaw=90,roll=0),True)
 actor.set_actor_scale3d(unreal.Vector((delta.length()+40)/100,1.4,thickness/100))
 REPORT['pieces'].append({'actor':actor.get_path_name(),'floor_start_cm':start.to_tuple(),'floor_finish_cm':finish.to_tuple(),'pitch_degrees':pitch})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
REPORT.update(success=True,backup=str(backup))
(OUT/'Sewer_Return_Ramp_Repair.json').write_text(json.dumps(REPORT,indent=2))
