"""Move the eleven existing Lab B pictures into the unobstructed entrance gallery.

Uses the measured wall bounds, preserves the original meshes/materials, backs up
the local map, and adds two local picture lights. Rendered/player acceptance is
separate; this report never claims a successful sightline from authoring alone.
"""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
MAP = '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB'
OUT = ROOT/'Saved/WorldExpansion'
PREFIX = 'WorldExpansion_WallArt_LabB_'
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError('Lab B failed to load')
subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {a.get_actor_label(): a for a in subsystem.get_all_level_actors()}
names = ['Portrait_01','Portrait_02','Portrait_05','Portrait_06','Portrait_08','Portrait_10',
         'Photo_01','Photo_02','Photo_03','Photo_04','Photo_05']
if any(PREFIX + name not in actors for name in names):
    raise RuntimeError('Expected all eleven existing art actors before moving any')
walls = {'north': actors['SM_MWall03-700x350-2'], 'south': actors['SM_MWall03-700x350-1']}
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
source = ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB.umap'
backup = OUT/'Backups'/('LabB_before_gallery_' + stamp + '.umap')
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, backup)
report = {'success': False, 'map': MAP, 'backup': str(backup), 'placements': [], 'lights': [],
          'acceptance': 'Saved authoring only; player travel, sightlines and rendered readability require the gallery PIE report.'}
specs = []
for side, group in [('north', names[:3]), ('south', names[3:6])]:
    for name, x in zip(group, [850., 1030., 1210.]):
        specs.append((name, side, x, 220.))
for name, x in zip(names[6:9], [880., 1060., 1240.]):
    specs.append((name, 'north', x, 135.))
for name, x in zip(names[9:], [950., 1150.]):
    specs.append((name, 'south', x, 135.))

for name, side, x, z in specs:
    actor = actors[PREFIX + name]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    previous = {'location': list(actor.get_actor_location().to_tuple()), 'rotation': list(actor.get_actor_rotation().to_tuple())}
    photo = name.startswith('Photo')
    yaw = (-90. if photo else 180.) if side == 'north' else (90. if photo else 0.)
    actor.set_actor_rotation(unreal.Rotator(pitch=0., yaw=yaw, roll=0.), False)
    center, extent = actor.get_actor_bounds(False, True)
    wc, we = walls[side].get_actor_bounds(False, True)
    face = wc.y - we.y if side == 'north' else wc.y + we.y
    y = face - .5 - extent.y if side == 'north' else face + .5 + extent.y
    desired = unreal.Vector(x,y,z)
    actor.set_actor_location(actor.get_actor_location() + desired - center, False, True)
    component.set_collision_profile_name('NoCollision')
    center, extent = actor.get_actor_bounds(False, True)
    if center.x-extent.x < 750 or center.x+extent.x > 1300 or center.z-extent.z < 70 or center.z+extent.z > 300:
        raise RuntimeError('Picture exceeds clear mounting panel: ' + name)
    report['placements'].append({'label': actor.get_actor_label(), 'wall': side, 'previous': previous,
        'center': list(center.to_tuple()), 'extent': list(extent.to_tuple()),
        'location': list(actor.get_actor_location().to_tuple()), 'rotation': list(actor.get_actor_rotation().to_tuple()),
        'mesh': component.get_editor_property('static_mesh').get_path_name(),
        'materials': [m.get_path_name() for m in component.get_materials() if m], 'wall_gap_cm': .5})

for side, pos, target in [('north',(1050.,560.,285.),(1050.,744.,190.)), ('south',(1050.,240.,285.),(1050.,56.,190.))]:
    label = 'WorldExpansion_ArtGallery_Light_' + side
    light = actors.get(label) or subsystem.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*pos))
    light.set_actor_label(label)
    light.set_actor_location(unreal.Vector(*pos), False, True)
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos), unreal.Vector(*target)), False)
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
    component.set_editor_property('intensity', 60.)
    component.set_editor_property('specular_scale', 0.)
    component.set_editor_property('source_width', 450.)
    component.set_editor_property('source_height', 45.)
    component.set_editor_property('attenuation_radius', 700.)
    component.set_editor_property('cast_shadows', False)
    component.set_light_color(unreal.LinearColor(r=.92,g=.96,b=1.,a=1.))
    report['lights'].append({'label': label, 'lumens': 60, 'specular_scale': 0, 'position': pos})

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError('Failed to save gallery map')
report['success'] = True
(OUT/'LabB_Gallery_Repair.json').write_text(json.dumps(report, indent=2))
print('LAB_B_GALLERY_REPAIR_SAVED')
unreal.SystemLibrary.quit_editor()
