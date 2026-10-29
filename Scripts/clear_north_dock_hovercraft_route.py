"""Move confirmed small lantern blockers onto supported side-pier verges.

The real hovercraft stalled against BP_Lamp_01a_C_5 at the side-pier entrance.
Survey both directions along the whole side pier; move only lanterns in our
North Dock copy, checking support and full-hull clearance before saving.
"""
import hashlib
import json
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
NAME = 'L_CarnivalWorldExpansion_DocksNorth_Layout'
LEVEL = ROOT / ('Content/Carnival/World/Levels/' + NAME + '.umap')
MAIN = ROOT / 'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT = ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
OUT = ROOT / 'Saved/WorldExpansion/WaterVehicleAcceptance/HovercraftPierClearance_20261029'
BACKUP = Path(r'D:\CarnivalBackups\hovercraft_pier_clearance_20261029')
OUT.mkdir(parents=True, exist_ok=False)
BACKUP.mkdir(parents=True, exist_ok=False)
V = unreal.Vector
N = unreal.DrawDebugTrace.NONE
R = {'success': False, 'errors': [], 'moved': [], 'collision_samples': 0}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def hit(raw):
    row = raw.to_tuple() if raw else None
    return row if row and row[0] else None


try:
    R['before'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    for target in (OUT / (NAME + '.before.umap'), BACKUP / (NAME + '.before.umap')):
        shutil.copy2(LEVEL, target)
        assert sha(target) == R['before'][LEVEL.name]
    world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    assert world
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ignore = [a for a in actors if a.get_actor_label().startswith('SM_Landscape_Far_01a')
              or isinstance(a, (unreal.CarnivalBoat, unreal.CarnivalHovercraft, unreal.PhysicsVolume))]

    def survey():
        blocked = {}
        for y in range(-48100, -55001, -100):
            for yaw in (-90, 90):
                sign = 1 if yaw == 90 else -1
                p = V(-50300, y, 735)
                h = hit(unreal.SystemLibrary.box_trace_single_by_profile(world, p, p + V(0, sign * 100, 0),
                    V(280, 205, 80), unreal.Rotator(pitch=-2.25, yaw=yaw), 'Vehicle', False, ignore, N, True))
                R['collision_samples'] += 1
                if h:
                    assert h[9], 'Collision without actor'
                    blocked[h[9].get_path_name()] = h[9]
        return blocked

    blockers = survey()
    assert blockers, 'Expected the recorded side-pier blockers'
    for actor in blockers.values():
        assert actor.get_actor_label() == 'NorthDock_Lantern' and '/' + NAME + '.' in actor.get_path_name(), actor.get_path_name()
        old = actor.get_actor_location()
        center, extent = actor.get_actor_bounds(False)
        bottom_offset = center.z - extent.z - old.z
        chosen = None
        for x in (-50850, -49750):
            p = V(x, old.y, old.z)
            floor = hit(unreal.SystemLibrary.line_trace_single(world, p + V(0, 0, 300), p - V(0, 0, 500),
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore + [actor], N, True))
            if not floor or floor[7].z < .9:
                continue
            if abs(floor[5].z - 635) > 2:
                continue
            body = V(x, old.y, floor[5].z + 30)
            occupied = hit(unreal.SystemLibrary.capsule_trace_single_by_profile(world, body, body + V(0, 0, .1),
                25, 25, 'Pawn', False, ignore + [actor], N, True))
            if not occupied:
                chosen = V(x, old.y, floor[5].z - bottom_offset + .5)
                break
        assert chosen, 'No supported verge for ' + actor.get_path_name()
        actor.modify()
        assert actor.set_actor_location(chosen, False, True)
        R['moved'].append({'actor': actor.get_path_name(), 'before_cm': old.to_tuple(),
            'after_cm': chosen.to_tuple(), 'support': floor[9].get_path_name(), 'bottom_above_support_cm': .5})
    remaining = survey()
    assert not remaining, list(remaining)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([actor.get_outermost()], False)
    R['after'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    for p in (MAIN, CONNECT):
        assert R['before'][p.name] == R['after'][p.name]
    shutil.copy2(LEVEL, BACKUP / LEVEL.name)
    assert sha(BACKUP / LEVEL.name) == R['after'][LEVEL.name]
    R.update(success=True, external_backup=str(BACKUP))
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(R, indent=2))
