"""Read-only bounds inventory around the measured lower-stair PIE obstruction."""
import json
from pathlib import Path
import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers')
point = (100., -852., 401.)
rows = []
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    center, extent = actor.get_actor_bounds(False, True)
    c, e = center.to_tuple(), extent.to_tuple()
    distance = sum(max(abs(point[i]-c[i])-e[i], 0.)**2 for i in range(3))**.5
    if distance > 250: continue
    components = []
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        components.append({'name': component.get_name(), 'collision': str(component.get_collision_enabled()),
            'mesh': str(component.get_editor_property('static_mesh')) if isinstance(component, unreal.StaticMeshComponent) else ''})
    rows.append({'name': actor.get_name(), 'label': actor.get_actor_label(), 'center': c, 'extent': e,
                 'distance_cm': distance, 'components': components})
Path(r'F:\Carnival\Saved\WorldExpansion\Sewer_Stair_Landing_Inspection.json').write_text(json.dumps(rows, indent=2))
unreal.SystemLibrary.quit_editor()
