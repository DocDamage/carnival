"""Read-only reflected ride and manager settings for lifecycle diagnosis."""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
assert world
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
rows = []
for actor in actors:
    name = actor.get_class().get_name()
    if not any(token in name for token in ('Clown', 'Manager', 'HotAir', 'Ferris', 'Carousel')):
        continue
    rows.append({'actor': actor.get_path_name(), 'class': name,
                 'controls': list(unreal.CarnivalRideOperationComponent.describe_ride_controls(actor)),
                 'properties': list(unreal.CarnivalRideOperationComponent.describe_ride_properties(actor))})
output = root/'Saved/RideDevelopment/ReflectedRideProperties.json'
output.write_text(json.dumps(rows, indent=2))
curve = unreal.load_asset('/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/C_HotairBalloonFloat')
if curve:
    samples = {str(t): list(curve.get_vector_value(t).to_tuple()) for t in (0,.25,.5,1,2,5,10,20,30,60)}
    try:
        samples['time_range'] = list(curve.get_time_range())
    except Exception as error:
        samples['time_range_error'] = repr(error)
    (root/'Saved/RideDevelopment/HotAirFloatCurve.json').write_text(json.dumps(samples, indent=2))
unreal.SystemLibrary.quit_editor()
