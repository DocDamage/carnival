"""Bridge the measured floor gap between the Atlantis hall and R12's mouth.

Only adds one project-owned floor piece in the backed-up connector level. The
real pawn round trip and rendered review must separately accept this repair.
"""
import datetime,json,math,shutil
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
evidence=OUT/'InteriorCameraAcceptance/ExpandedCorridors_20260929.json'
case=next(c for c in json.loads(evidence.read_text())['cases'] if c['name']=='atlantis_hall')
assert case.get('error')=='Endpoint height/floor mismatch after settling'
end=case['legs'][-1]['endpoint_floor_probe']
assert end['actor']=='AtlantisToShipwreckPassage_Walkway' and not end['initial_overlap']
PACKAGE='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout'
file=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
backup=OUT/'Backups'/('Connections_before_atlantis_floor_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.umap')
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(PACKAGE);assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=list(actors.get_all_level_actors())
reference=next(a for a in rows if a.get_name()=='StaticMeshActor_994')
component=reference.get_component_by_class(unreal.StaticMeshComponent)
assert reference.get_actor_label()=='AtlantisToShipwreckPassage_Walkway'
assert unreal.Vector.distance(reference.get_actor_location(),unreal.Vector(-6750,-10750,-1917.5))<1000
label='AtlantisHall_R12_FloorHandoff';tag=unreal.Name('CarnivalInteriorHandoffRepair')
actor=next((a for a in rows if a.get_actor_label()==label),None)
assert not actor or tag in actor.tags,'Refusing unrelated actor replacement'
cube=unreal.load_asset('/Engine/BasicShapes/Cube');assert cube
if not actor: actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
actor.modify();actor.set_actor_label(label);actor.set_editor_property('tags',[tag])
mesh=actor.get_component_by_class(unreal.StaticMeshComponent);mesh.modify()
mesh.set_static_mesh(cube);mesh.set_mobility(unreal.ComponentMobility.STATIC)
mesh.set_collision_profile_name('BlockAll');mesh.set_material(0,component.get_material(0))
start=unreal.Vector(-7500,-11600,-1750);finish=unreal.Vector(*end['point_cm'])
delta=finish-start;horizontal=math.hypot(delta.x,delta.y)
pitch=math.degrees(math.atan2(delta.z,horizontal));yaw=math.degrees(math.atan2(delta.y,delta.x))
length=delta.length()+40;thickness=35
center=(start+finish)*.5-unreal.Vector(0,0,thickness*.5*math.cos(math.radians(pitch)))
actor.set_actor_location(center,False,True);actor.set_actor_rotation(unreal.Rotator(pitch=pitch,yaw=yaw,roll=0),True)
actor.set_actor_scale3d(unreal.Vector(length/100,4.2,thickness/100))
assert abs(pitch)<5
assert unreal.EditorLoadingAndSavingUtils.save_map(world,PACKAGE)
REPORT={'success':True,'backup':str(backup),'evidence':str(evidence),'actor':actor.get_path_name(),
    'start_top_cm':start.to_tuple(),'end_top_cm':finish.to_tuple(),'pitch_deg':pitch,
    'acceptance':'Saved geometry only; requires actual pawn continuous round trip/camera and rendered review.'}
(OUT/'Atlantis_Passage_Floor_Repair.json').write_text(json.dumps(REPORT,indent=2))
