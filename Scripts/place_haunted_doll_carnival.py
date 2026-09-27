"""Place one encounter beside the haunted-house queue, retaining a map backup."""
import json, math, shutil
from pathlib import Path
import unreal

BASE='/Game/Carnival/Characters/PossessedDoll'
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
backup=OUT/'Backups/LV_Carnival.before_doll.umap';backup.parent.mkdir(exist_ok=True)
source=Path(r'F:\Carnival\Content\Creepwood_Carnival_Meshingun\Environment\Map\LV_Carnival.umap')
if not backup.exists():shutil.copy2(source,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tag='Carnival.HauntedDoll.MainEncounter'
existing=[a for a in eas.get_all_level_actors() if tag in [str(t) for t in a.tags]]
assert len(existing)<=1
bp=unreal.load_asset(BASE+'/BP_PossessedDoll')
report={'map':MAP,'backup':str(backup),'clearance':[]}
chosen=None
for x,y in [(8000,4950),(8100,5050),(7900,5150),(8000,5350)]:
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,350),unreal.Vector(x,y,-100),unreal.TraceTypeQuery.ECC_VISIBILITY,False,existing,unreal.DrawDebugTrace.NONE,True)
    if not hit:continue
    data=hit.to_tuple()
    if not data[0] or data[7].z<.9:continue
    ground=data[5];position=unreal.Vector(x,y,ground.z+74)
    overlap=unreal.SystemLibrary.capsule_trace_single(world,position,position+unreal.Vector(0,0,.1),28,71,unreal.TraceTypeQuery.ECC_VISIBILITY,False,existing,unreal.DrawDebugTrace.NONE,True)
    blocked=bool(overlap and overlap.to_tuple()[0])
    goal=unreal.Vector(7600,y+150,position.z)
    passage=unreal.SystemLibrary.capsule_trace_single(world,position,goal,28,71,unreal.TraceTypeQuery.ECC_VISIBILITY,False,existing,unreal.DrawDebugTrace.NONE,True)
    clear_path=not(passage and passage.to_tuple()[0])
    report['clearance'].append({'position':[position.x,position.y,position.z],'capsule_clear':not blocked,'approach_clear':clear_path})
    if not blocked and clear_path:
        chosen=(position,math.degrees(math.atan2(goal.y-y,goal.x-x)))
        break
assert chosen,'No verified clear placement point beside the haunted house.'
position,yaw=chosen
if existing:
    doll=existing[0]
    doll.modify();doll.get_editor_property('root_component').modify()
    doll.set_actor_location(position,False,False);doll.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
else:doll=eas.spawn_actor_from_class(bp.generated_class(),position,unreal.Rotator(pitch=0,yaw=yaw,roll=0))
assert doll and doll.get_component_by_class(unreal.SkeletalMeshComponent).get_skeletal_mesh_asset()
doll.set_actor_label('PossessedDoll_HauntedHouse')
doll.set_folder_path('Carnival/Haunted Doll')
doll.tags=list(set([str(t) for t in doll.tags]+[tag]))
doll.set_editor_property('encounter_enabled',True)
assert abs(doll.get_actor_rotation().pitch)<.01 and abs(doll.get_actor_rotation().roll)<.01
assert unreal.EditorLoadingAndSavingUtils.save_map(world,MAP)
report.update({'actor':doll.get_path_name(),'location':[position.x,position.y,position.z],'yaw':yaw,'blueprint':bp.get_path_name()})
(OUT/'Carnival_Placement.json').write_text(json.dumps(report,indent=2))
unreal.log_warning('DOLL_CARNIVAL_PLACEMENT_COMPLETE')
