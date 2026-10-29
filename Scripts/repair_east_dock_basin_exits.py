"""Add supported return slipways to the two eastern boatyard basin pockets.

The 2026-10-29 reachability audit found 1,174 reachable basin cells without a
walking return. Existing slipways serve the west side of the elevated spine.
Only the East Dock copy is saved, with hash-verified local and D: backups.
Run a fresh reachability audit and real-character walks after this authoring.
"""
import hashlib
import json
import math
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
NAME = 'L_CarnivalWorldExpansion_DocksEast'
LEVEL = ROOT / ('Content/Carnival/World/Levels/' + NAME + '.umap')
MAIN = ROOT / 'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT = ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
OUT = ROOT / 'Saved/WorldExpansion/EastDockBasinExits_20261029_v2'
BACKUP = Path(r'D:\CarnivalBackups\east_dock_basin_exits_20261029_v2')
OUT.mkdir(parents=True, exist_ok=False)
BACKUP.mkdir(parents=True, exist_ok=False)
V = unreal.Vector
N = unreal.DrawDebugTrace.NONE
R = {'success': False, 'errors': [], 'ramps': []}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def hit(raw):
    value = raw.to_tuple() if raw else None
    return value if value and value[0] else None


try:
    R['before'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    for dest in (OUT / (NAME + '.before.umap'), BACKUP / (NAME + '.before.umap')):
        shutil.copy2(LEVEL, dest)
        assert sha(dest) == R['before'][LEVEL.name]
    world = unreal.EditorLoadingAndSavingUtils.load_map(
        '/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    assert world
    ea = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = ea.get_all_level_actors()
    labels = {a.get_actor_label() for a in actors}
    assert not any(label.startswith('EastDock_Boatyard_ReturnSlipway_') for label in labels)
    ignore = [a for a in actors if a.get_actor_label().startswith('SM_Landscape_Far_01a')
              or isinstance(a, unreal.PhysicsVolume)]
    assert le.set_current_level_by_name(NAME)
    mesh = unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
    material = unreal.load_asset('/Game/Docks/VOL2_Powell/Materials/Instances/MI_Wooden_Planks_Beams_01')
    assert mesh and material
    run, rise, thick, y0 = 1000.0, 85.0, 30.0, 18850.0
    angle = math.degrees(math.atan2(rise, run))
    for suffix, x, width in (('InnerEast', 72300.0, 400.0), ('OuterEast', 73700.0, 500.0)):
        center = V(x, y0 + run / 2 + thick / 2 * math.sin(math.radians(angle)),
                   560 + rise / 2 - thick / 2 * math.cos(math.radians(angle)))
        ramp = None
        for sign in (1, -1):
            if ramp:
                ea.destroy_actor(ramp)
            ramp = ea.spawn_actor_from_class(unreal.StaticMeshActor, center,
                                            unreal.Rotator(yaw=90, pitch=sign * angle))
            assert ramp and '/' + NAME + '.' in ramp.get_path_name()
            ramp.static_mesh_component.set_static_mesh(mesh)
            ramp.static_mesh_component.set_material(0, material)
            ramp.static_mesh_component.set_collision_profile_name('BlockAll')
            ramp.set_actor_scale3d(V((run / math.cos(math.radians(angle)) + 10) / 100,
                                     width / 100, thick / 100))
            ramp.set_actor_label('EastDock_Boatyard_ReturnSlipway_' + suffix)
            ramp.set_folder_path('EastDock_Boatyard')
            ramp.tags = [unreal.Name('CarnivalBoatyard'), unreal.Name('CarnivalBasinReturn')]
            low = hit(unreal.SystemLibrary.line_trace_single(world, V(x, y0 + 940, 900),
                      V(x, y0 + 940, 300), unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, N, True))
            high = hit(unreal.SystemLibrary.line_trace_single(world, V(x, y0 + 60, 900),
                       V(x, y0 + 60, 300), unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, N, True))
            if low and high and low[9] == ramp and high[9] == ramp and low[5].z < high[5].z:
                break
        assert low and high and low[9] == ramp and high[9] == ramp
        assert abs(low[5].z - 565.1) < 5 and abs(high[5].z - 639.9) < 5
        row = {'label': ramp.get_actor_label(), 'center_cm': center.to_tuple(),
               'width_cm': width, 'slope_degrees': angle, 'samples': []}
        # Three lanes, including the basin and quay beyond the ramp ends.
        # Object traces include invisible fence caps that ignore Visibility.
        for dx in (-width / 2 + 60, 0, width / 2 - 60):
            previous = None
            for dy in range(-150, 1151, 25):
                p = V(x + dx, y0 + dy, 900)
                floor = hit(unreal.SystemLibrary.line_trace_single(world, p, p - V(0, 0, 600),
                            unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, N, True))
                assert floor and floor[7].z > .9, (suffix, dx, dy, 'floor')
                foot = floor[5]
                body = foot + V(0, 0, 100)
                blocked = hit(unreal.SystemLibrary.capsule_trace_single_by_profile(
                    world, body, body + V(0, 0, .1), 42, 96, 'Pawn', False, ignore, N, True))
                assert not blocked, (suffix, dx, dy, blocked[9].get_path_name() if blocked and blocked[9] else 'collision')
                if previous is not None:
                    assert abs(foot.z - previous.z) < 10, (suffix, 'surface discontinuity')
                previous = foot
                row['samples'].append({'foot_cm': foot.to_tuple(), 'floor': floor[9].get_actor_label()})
        R['ramps'].append(row)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([ramp.get_outermost()], False)
    R['after'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    assert R['after'][MAIN.name] == R['before'][MAIN.name]
    assert R['after'][CONNECT.name] == R['before'][CONNECT.name]
    shutil.copy2(LEVEL, BACKUP / LEVEL.name)
    assert sha(BACKUP / LEVEL.name) == R['after'][LEVEL.name]
    R.update(success=True, external_backup=str(BACKUP))
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(R, indent=2))
