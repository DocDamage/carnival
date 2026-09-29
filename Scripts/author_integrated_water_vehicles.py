"""Apply a surveyed, idempotent vehicle/boarding plan only to project-owned maps.

Requires Saved/WorldExpansion/WaterVehicleAcceptance/PlacementPlan.json with
survey_sha256 matching main_PlacementSurvey.json. Plan entries use local map
transforms and explicit collision geometry; no vendor map or mesh is modified.
"""
import datetime,hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance'
PLAN=OUT/'PlacementPlan.json'; SURVEY=OUT/'main_PlacementSurvey.json'
report={'success':False,'backups':[],'vehicles':[],'saved_maps':[],'errors':[],'acceptance':'Saved authoring only; requires actual pawn boarding, drive, continuous return, unloading and rendered review.'}
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
TAG=unreal.Name('CarnivalSurveyedWaterVehicle')

def vector(p): return unreal.Vector(*[float(v) for v in p])
def marked(actor): return TAG in actor.get_editor_property('tags')
def obtain(label,cls,existing):
    actor=existing.get(label)
    if actor and (not marked(actor) or not isinstance(actor,cls)): raise RuntimeError('Refusing to overwrite unrelated '+label)
    if not actor: actor=eas.spawn_actor_from_class(cls,unreal.Vector(0,0,0))
    actor.set_actor_label(label); actor.set_editor_property('tags',[TAG]); return actor
try:
    plan=json.loads(PLAN.read_text()); survey=json.loads(SURVEY.read_text())
    if not survey.get('success') or not survey.get('collision_positive_controls_passed'): raise RuntimeError('Runtime collision survey not valid')
    if hashlib.sha256(SURVEY.read_bytes()).hexdigest()!=plan['survey_sha256']: raise RuntimeError('Plan survey hash is stale')
    if plan.get('depth_survey_sha256') and hashlib.sha256((OUT/'DockWaterDepth.json').read_bytes()).hexdigest()!=plan['depth_survey_sha256']: raise RuntimeError('Plan depth/drive-lane survey hash is stale')
    if plan.get('berth_survey_sha256') and hashlib.sha256((OUT/'DockWaterBerth.json').read_bytes()).hexdigest()!=plan['berth_survey_sha256']: raise RuntimeError('Plan dense boat-berth survey hash is stale')
    if not plan.get('entries'): raise RuntimeError('No surveyed placement entries')
    labels=[e['label'] for e in plan['entries']]
    if len(set(labels))!=len(labels): raise RuntimeError('Duplicate planned vehicle labels')
    # Preflight every destination and required asset before writing any package.
    for entry in plan['entries']:
        package=entry['map']
        if not package.startswith('/Game/Carnival/World/Levels/'): raise RuntimeError('Only project-owned level copies may be edited')
        if not (ROOT/('Content/'+package.removeprefix('/Game/')+'.umap')).exists(): raise RuntimeError('Missing copied destination '+package)
        if entry['kind'] not in ('boat','hovercraft'): raise RuntimeError('Unknown vehicle kind')
        if not unreal.EditorAssetLibrary.does_asset_exist(entry['mesh']): raise RuntimeError('Missing vehicle mesh '+entry['mesh'])
        if entry.get('boarding_survey_evidence') is None or len(entry.get('approach_world_cm',[]))<2: raise RuntimeError('Missing measured boarding approach')
        if entry['kind']=='boat' and not entry.get('water_survey_evidence'): raise RuntimeError('Boat requires measured water surface evidence')
        if entry['kind']=='boat' and (not entry.get('navigable_water_min_world_cm') or not entry.get('navigable_water_max_world_cm')): raise RuntimeError('Boat requires measured navigable water bounds')
        if not entry.get('drive_lane_survey_evidence') or entry.get('drive_distance_cm',0)<1000: raise RuntimeError('Vehicle requires a measured drive lane of at least 10 m')
        if not entry.get('checkpoints_world_cm'): raise RuntimeError('Activity requires measured checkpoints')
        for size in (entry['collision_half_extent_cm'],entry['mount_half_extent_cm']):
            if len(size)!=3 or not all(math.isfinite(float(v)) and float(v)>0 for v in size): raise RuntimeError('Invalid collision/mount dimensions')
        for segment in entry.get('boarding_decks',[]):
            size=segment['size_cm']; pitch=abs(segment.get('rotation_deg',[0,0,0])[0])
            if min(size)<=0 or size[1]<250 or pitch>25: raise RuntimeError('Unsafe boarding deck dimensions/slope')
        for p in entry['approach_world_cm']+entry['checkpoints_world_cm']+[entry['location_local_cm'],entry['activity_location_local_cm']]:
            if len(p)!=3 or not all(math.isfinite(float(v)) for v in p): raise RuntimeError('Invalid approach coordinates')
    for package in sorted({e['map'] for e in plan['entries']}):
        filename=ROOT/('Content/'+package.removeprefix('/Game/')+'.umap')
        if not filename.exists(): raise RuntimeError('Missing copied destination '+package)
        backup=OUT/(filename.stem+'_before_vehicles_'+stamp+'.umap'); shutil.copy2(filename,backup); report['backups'].append(str(backup))
        world=unreal.EditorLoadingAndSavingUtils.load_map(package)
        if not world: raise RuntimeError('Cannot load '+package)
        existing={a.get_actor_label():a for a in eas.get_all_level_actors()}
        for entry in [e for e in plan['entries'] if e['map']==package]:
            cls=unreal.CarnivalBoat if entry['kind']=='boat' else unreal.CarnivalHovercraft
            actor=obtain(entry['label'],cls,existing)
            actor.set_actor_location(vector(entry['location_local_cm']),False,True)
            actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=entry['yaw_local_deg'],roll=0),True)
            comp=actor.get_editor_property('boat_mesh' if entry['kind']=='boat' else 'craft_mesh')
            comp.set_static_mesh(unreal.load_asset(entry['mesh']))
            comp.set_relative_scale3d(vector(entry.get('mesh_scale',[1,1,1])))
            comp.set_relative_rotation(unreal.Rotator(pitch=0,yaw=entry.get('mesh_yaw_deg',0),roll=0),False,True)
            actor.get_editor_property('collision_box').set_box_extent(vector(entry['collision_half_extent_cm']),True)
            actor.get_editor_property('mount_trigger').set_box_extent(vector(entry['mount_half_extent_cm']),True)
            if entry.get('driver_relative_offset_cm'):
                actor.set_editor_property('driver_relative_offset',vector(entry['driver_relative_offset_cm']))
            if entry['kind']=='boat':
                actor.set_editor_property('auto_detect_water',False)
                # Native boat plane is absolute world Z, not sublevel-local Z.
                actor.set_editor_property('water_plane_z',float(entry['water_plane_world_z']))
                actor.set_editor_property('use_navigable_water_bounds',True)
                actor.set_editor_property('navigable_water_min',unreal.Vector2D(*entry['navigable_water_min_world_cm']))
                actor.set_editor_property('navigable_water_max',unreal.Vector2D(*entry['navigable_water_max_world_cm']))
                actor.set_editor_property('minimum_keel_clearance',float(entry.get('minimum_keel_clearance_cm',25)))
            for i,segment in enumerate(entry.get('boarding_decks',[])):
                deck=obtain(entry['label']+'_BoardingDeck_'+str(i),unreal.StaticMeshActor,existing)
                deck.set_actor_location(vector(segment['center_local_cm']),False,True)
                deck.set_actor_scale3d(vector([v/100 for v in segment['size_cm']]))
                p,y,r=segment.get('rotation_deg',[0,0,0]); deck.set_actor_rotation(unreal.Rotator(pitch=p,yaw=y,roll=r),True)
                c=deck.get_component_by_class(unreal.StaticMeshComponent); c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
                c.set_collision_profile_name('BlockAll')
                if segment.get('material'): c.set_material(0,unreal.load_asset(segment['material']))
                elif segment.get('material_from_actor'):
                    reference=existing.get(segment['material_from_actor'])
                    if not reference: raise RuntimeError('Missing boarding deck material source')
                    material=reference.get_component_by_class(unreal.StaticMeshComponent).get_material(0)
                    if not material: raise RuntimeError('Boarding deck source has no material')
                    c.set_material(0,material)
            activity=obtain(entry['label']+'_HandlingActivity',unreal.CarnivalActivityBase,existing)
            activity.set_actor_location(vector(entry['activity_location_local_cm']),False,True)
            activity.set_editor_property('activity_name',entry['activity_name'])
            activity.set_editor_property('description',entry['activity_description'])
            activity.set_editor_property('activity_type',unreal.CarnivalChallengeType.STUNT_RALLY)
            activity.set_editor_property('time_limit',float(entry.get('time_limit',120)))
            cps=[]
            for point in entry['checkpoints_world_cm']:
                cp=unreal.CarnivalActivityCheckpoint(); cp.set_editor_property('location',vector(point)); cp.set_editor_property('radius',float(entry.get('checkpoint_radius_cm',400))); cps.append(cp)
            activity.set_editor_property('checkpoints',cps); activity.set_editor_property('target_score',len(cps)*100)
            report['vehicles'].append({'label':entry['label'],'map':package,'actor':actor.get_path_name(),'activity':activity.get_path_name(),'authored_transform_cm':entry['location_local_cm']})
        if not unreal.EditorLoadingAndSavingUtils.save_map(world,package): raise RuntimeError('Cannot save '+package)
        report['saved_maps'].append(package)
    report['success']=True; report['plan_sha256']=hashlib.sha256(PLAN.read_bytes()).hexdigest()
except Exception:
    report['errors'].append(traceback.format_exc()); unreal.log_error(report['errors'][-1])
finally:
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'Authoring.json').write_text(json.dumps(report,indent=2)); unreal.SystemLibrary.quit_editor()
