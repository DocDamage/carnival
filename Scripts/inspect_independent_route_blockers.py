"""Resolve blockers concealed by support-floor traces to component geometry."""
import json
from pathlib import Path
import unreal
root=Path(r'F:\Carnival')
audit=json.loads((root/'Saved/WorldExpansion/Route_Collision_Audit.json').read_text())
hits={h['actor_path']:h for route in audit['routes'] for h in route.get('independent_clearance_obstructions',[])}
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
rows=[]
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_path_name() not in hits: continue
    center,extent=actor.get_actor_bounds(False,True)
    row={'label':actor.get_actor_label(),'path':actor.get_path_name(),'location':actor.get_actor_location().to_tuple(),'center':center.to_tuple(),'extent':extent.to_tuple(),'components':[]}
    hit=unreal.Vector(*hits[actor.get_path_name()]['point_cm'])
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh=comp.get_editor_property('static_mesh')
        pos=comp.get_world_location()
        if (pos-hit).length()>10000: continue
        row['components'].append({'name':comp.get_name(),'mesh':mesh.get_path_name() if mesh else None,'position':pos.to_tuple(),'collision':str(comp.get_collision_enabled())})
    rows.append(row)
(root/'Saved/WorldExpansion/Independent_Blocker_Details.json').write_text(json.dumps(rows,indent=2))
unreal.SystemLibrary.quit_editor()
