"""Clear the Mansion departure and regenerate the terrain-safe outer route."""
import datetime
import math
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / 'Saved/WorldExpansion'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
packages = ['/Game/Carnival/World/Levels/L_HauntedMansionConnected',
            '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout']
backups = []
for package in packages:
    source = ROOT / ('Content/' + package.removeprefix('/Game/') + '.umap')
    dest = OUT / 'Backups' / (source.stem + '_before_clearance_' + stamp + '.umap')
    shutil.copy2(source, dest)
    backups.append(str(dest))
region_path = OUT / 'Region_Authoring.json'
shutil.copy2(region_path, OUT / 'Backups' / ('Region_Authoring_before_clearance_' + stamp + '.json'))

# Resolve world-space moves against the streaming transform, then apply them
# in the standalone copied Mansion map. Licensed source meshes are unchanged.
root_world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
stream = unreal.GameplayStatics.get_streaming_level(root_world, 'L_HauntedMansionConnected')
transform = stream.get_editor_property('level_transform')
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
targets = {}
previous_path = OUT / 'Outer_Clearance_Repair.json'
previous = json.loads(previous_path.read_text()).get('moved_actors', {}) if previous_path.exists() else {}
for actor in eas.get_all_level_actors():
    if actor.get_actor_label() not in ('SM_StoneFence33', 'SM_StoneFence36', 'SM_StoneFence37', 'SM_StoneFence45', 'SM_Plate2', 'SM_Plate3', 'SM_EuropeanBeech_XL_29') or 'L_HauntedMansionConnected' not in actor.get_path_name():
        continue
    before = unreal.Vector(*previous[actor.get_name()]['before_world']) if actor.get_name() in previous else actor.get_actor_location()
    offset = 1500. if actor.get_actor_label() == 'SM_EuropeanBeech_XL_29' else 850.
    after = before + unreal.Vector(0., offset, 0.)
    if actor.get_actor_label() in ('SM_StoneFence33','SM_Plate2'):
        after = before + unreal.Vector(-1500., 0., 0.)
    local = unreal.MathLibrary.inverse_transform_location(transform, after)
    targets[actor.get_name()] = {'label': actor.get_actor_label(), 'before_world': before.to_tuple(), 'after_world': after.to_tuple(), 'after_local': local.to_tuple()}
if len(targets) != 7:
    raise RuntimeError('Expected the five Mansion blockers and their two sign plates')
world = unreal.EditorLoadingAndSavingUtils.load_map(packages[0])
for actor in eas.get_all_level_actors():
    if actor.get_name() in targets:
        actor.set_actor_location(unreal.Vector(*targets[actor.get_name()]['after_local']), False, True)
if not unreal.EditorLoadingAndSavingUtils.save_map(world, packages[0]):
    raise RuntimeError('Could not save copied Mansion map')
region = json.loads(region_path.read_text())
start = region['outer_route_spine']['controls_cm'][0]
# End on the existing tested paved forecourt, six metres before the door.
end = [95658.631343663,128400.316903534,642.781]
controls = [start, [-69000.,-83500.,650.], [-67500.,-83300.,700.],
            [-65000.,-84000.,850.], [-54000.,-84000.,1400.],
            [-53000.,-84000.,1400.], [-54000.,-70000.,1000.],
            [-55000.,-55000.,680.], [-50000.,-46000.,700.],
            [-43000.,-38000.,600.], [-35000.,-30000.,600.],
            [-30000.,-25000.,600.], [-25000.,-22000.,600.],
            [-15000.,-18000.,600.], [0.,-17000.,600.],
            [20000.,-6000.,600.], [35000.,0.,600.],
            [50000.,8000.,650.], [70000.,18000.,650.]]
# Evenly spaced controls prevent Catmull endpoint overshoot: the former
# 1 km penultimate span bent the last 60 m back through the hospital interior.
approach = [92322.7875,124149.1820,640.]
a = controls[-1]
count = math.ceil(math.dist(a,approach)/10000.)
controls += [[a[k]+(approach[k]-a[k])*i/count for k in range(3)] for i in range(1,count+1)]
controls.append(end)
region['outer_route_spine']['controls_cm'] = controls
region_path.write_text(json.dumps(region, indent=2))
source = (ROOT / 'Scripts/repair_world_expansion_route_alignment.py').read_text()
exec(source.replace('unreal.SystemLibrary.quit_editor()', ''), {})
(OUT / 'Outer_Clearance_Repair.json').write_text(json.dumps({'success': True, 'backups': backups, 'moved_actors': targets, 'terrain_shelf_control_z_cm': 1400., 'acceptance': 'Pending fresh static audit and PIE'}, indent=2))
unreal.SystemLibrary.quit_editor()
