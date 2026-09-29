"""Seat frames against traced walls, falling back to actual transformed mesh bounds."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

root=Path(r'F:\Carnival')
out=root/'Saved/WorldExpansion'
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB'
source=root/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB.umap'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=out/'Backups'/('L_CarnivalWorldExpansion_LabB_before_frame_depth_'+stamp+'.umap')
shutil.copy2(source,backup)
placement_path=out/'HorrorPaintVol48_LabB_WallArt_Placement.json'
shutil.copy2(placement_path,out/'Backups'/('LabB_Placements_before_frame_depth_'+stamp+'.json'))
placements=json.loads(placement_path.read_text())
world=unreal.EditorLoadingAndSavingUtils.load_map(package)
actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
walls=[]
for actor in actors:
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh=comp.get_editor_property('static_mesh') if comp else None
    if mesh and 'mwall' in mesh.get_name().lower(): walls.append(actor)
if not walls: raise RuntimeError('No modular wall meshes found')
ignore=[a for a in actors if a not in walls]
changes=[]
by_label={a.get_actor_label():a for a in actors}
for p in placements['placements']:
    actor=by_label[p['label']]
    center,extent=actor.get_actor_bounds(False,True)
    hits=[]
    for dx,dz in [(0,0),(-extent.x*.9,0),(extent.x*.9,0),(0,-extent.z*.9),(0,extent.z*.9)]:
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(center.x+dx,1300.,center.z+dz),unreal.Vector(center.x+dx,1550.,center.z+dz),unreal.TraceTypeQuery.ECC_VISIBILITY,True,ignore,unreal.DrawDebugTrace.NONE,True)
        values=hit.to_tuple() if hit else None
        if values and values[0]:
            hits.append({'y':values[5].y,'actor':values[9].get_actor_label(),'method':'complex trace'})
        else:
            # These source wall meshes have no complex query collision. Use
            # their actual transformed bounds, including the offset mesh pivot.
            candidates=[]
            for wall in walls:
                wc,we=wall.get_actor_bounds(False,True)
                if we.y<50 and wc.y>1400 and abs(center.x+dx-wc.x)<=we.x and abs(center.z+dz-wc.z)<=we.z:
                    candidates.append((wc.y-we.y,wall.get_actor_label()))
            if not candidates: raise RuntimeError('No wall bounds behind '+p['label'])
            y,label=min(candidates)
            hits.append({'y':y,'actor':label,'method':'actual transformed wall bounds; complex collision unavailable'})
    wall_y=min(h['y'] for h in hits)
    target_back=wall_y-.5
    if abs(target_back-(center.y+extent.y))>25.: raise RuntimeError('Unexpected wall depth; review '+p['label'])
    before=actor.get_actor_location()
    actor.set_actor_location(before+unreal.Vector(0,target_back-(center.y+extent.y),0),False,True)
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_collision_profile_name('NoCollision')
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    center,extent=actor.get_actor_bounds(False,True)
    p.update(actual_location_cm=actor.get_actor_location().to_tuple(),bounds_center_cm=center.to_tuple(),bounds_extent_cm=extent.to_tuple(),wall_face_y_cm=wall_y,wall_edge_y_cm=center.y+extent.y,wall_gap_cm=.5)
    changes.append({'label':p['label'],'before':before.to_tuple(),'after':actor.get_actor_location().to_tuple(),'wall_hits':hits,'collision':str(comp.get_collision_enabled())})
if len(changes)!=11: raise RuntimeError('Expected all eleven original frames')
if not unreal.EditorLoadingAndSavingUtils.save_map(world,package): raise RuntimeError('Lab B save failed')
placement_path.write_text(json.dumps(placements,indent=2))
(out/'LabB_Frame_Depth_Repair.json').write_text(json.dumps({'success':True,'backup':str(backup),'changes':changes,'visual_acceptance':'Requires post-save PIE capture; machinery sightlines remain separate.'},indent=2))
unreal.SystemLibrary.quit_editor()
