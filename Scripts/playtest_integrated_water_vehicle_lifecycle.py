"""Exercise a real saved boat/hovercraft from a surveyed approach, with no fixtures.

Run using run_doll_tool.py playtest after author_integrated_water_vehicles.py.
CARNIVAL_VEHICLE_LABEL selects one PlacementPlan entry (defaults to first).
The driver follows a straight measured clearance lane and reverses continuously
to the boarding location; no mid-test actor repositioning or time acceleration.
"""
import hashlib,json,math,os,time,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance'
PLAN=OUT/'PlacementPlan.json'; AUTHOR=OUT/'Authoring.json'
plan=json.loads(PLAN.read_text()); authored=json.loads(AUTHOR.read_text())
digest=hashlib.sha256(PLAN.read_bytes()).hexdigest()
if not authored.get('success') or authored.get('plan_sha256')!=digest:
    raise RuntimeError('Requires successful authoring of this exact plan')
label=os.environ.get('CARNIVAL_VEHICLE_LABEL',plan['entries'][0]['label'])
entry=next(e for e in plan['entries'] if e['label']==label)
# Clearance evidence is required separately from the boarding/water-plane probe.
if not entry.get('drive_lane_survey_evidence') or entry.get('drive_distance_cm',0)<1000:
    raise RuntimeError('Plan needs a measured clear drive lane of at least 10 m')
if not label.replace('_','').isalnum(): raise ValueError('Unsafe report label')
report={'success':False,'vehicle':label,'kind':entry['kind'],'plan_sha256':digest,
        'errors':[],'samples':[],'events':[],'excluded_spawners':[],
        'scope':'Real saved vehicle: walk approach, contextual mount, powered outbound, continuous reverse return, ordinary safe unload and walk back.',
        'limits':'Direct movement/control APIs, no physical gamepad. This short clearance lane does not accept an entire activity course, all water boundaries, rendered presentation or performance.'}
OUT.mkdir(parents=True,exist_ok=True)
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
state={'phase':'setup','deadline':time.monotonic()+240,'busy':False}

def vec(p): return unreal.Vector(*[float(x) for x in p])
def xy(a,b): return math.hypot(a.x-b.x,a.y-b.y)
def write():
    report['phase']=state['phase']; report['timestamp']=time.time()
    (OUT/(label+'_Lifecycle.json')).write_text(json.dumps(report,indent=2))
def event(name,**details):
    report['events'].append({'name':name,'seconds':unreal.GameplayStatics.get_time_seconds(state['game']),**details}); write()
def floor(p,ignore):
    h=unreal.SystemLibrary.line_trace_single(state['game'],p+unreal.Vector(0,0,100),p-unreal.Vector(0,0,300),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignore,unreal.DrawDebugTrace.NONE,True)
    h=h.to_tuple() if h else None
    if not h or not h[0]: return None
    return {'point_cm':h[5].to_tuple(),'normal':h[7].to_tuple(),'initial_overlap':bool(h[1]),'actor':h[9].get_actor_label() if h[9] else None}
def finish(error=None):
    if error: report['errors'].append(error)
    if state.get('vehicle'): state['vehicle'].clear_control_inputs()
    if state.get('pawn'): state['pawn'].get_movement_component().stop_movement_immediately()
    report['success']=not report['errors']; write(); le.editor_request_end_play()
    state.update(phase='exit',deadline=time.monotonic()+3)
def walk_begin(points,phase):
    position=state['pawn'].get_actor_location()
    state.update(phase=phase,path=points,index=0,segment_start=position-unreal.Vector(0,0,state['half']),
        progress=position,progress_time=time.monotonic(),deadline=time.monotonic()+120,last_walk_sample=0)
def speed():
    prop='current_speed' if entry['kind']=='boat' else 'current_forward_speed'
    return abs(float(state['vehicle'].get_editor_property(prop)))
def check_ground(p):
    f=floor(p,[state['pawn'],state['vehicle']]); m=state['pawn'].get_movement_component()
    return f if f and not f['initial_overlap'] and f['normal'][2]>.7 and m.is_moving_on_ground() and abs(p.z-f['point_cm'][2]-state['half'])<45 else None

def return_path_after_unload(pos):
    # Hovercraft unloads on either clear side of its hull. Reversing the arrival
    # markers can send a left-side passenger straight through the parked craft
    # to the right-side boarding marker. Follow the actual hull's rear perimeter
    # on the existing pier, checking real Pawn collision and floor first.
    if entry['kind']!='hovercraft': return list(reversed(state['approach']))
    vehicle=state['vehicle'];transform=vehicle.get_actor_transform()
    capsule=state['pawn'].get_component_by_class(unreal.CapsuleComponent)
    radius=capsule.get_scaled_capsule_radius()
    extent=vehicle.get_editor_property('collision_box').get_scaled_box_extent()
    local=unreal.MathLibrary.inverse_transform_location(transform,pos)
    destination=unreal.MathLibrary.inverse_transform_location(transform,state['approach'][0])
    side=1 if local.y>=0 else -1; end_side=1 if destination.y>=0 else -1
    back=extent.x+radius+150; width=extent.y+radius+150
    markers=[unreal.MathLibrary.transform_location(transform,unreal.Vector(-back,side*width,0))]
    if side!=end_side:
        markers.append(unreal.MathLibrary.transform_location(transform,unreal.Vector(-back,end_side*width,0)))
    markers.append(state['approach'][0])
    path=[]; previous=pos; checks=[]
    for marker in markers:
        ground=floor(marker,[state['pawn'],vehicle])
        if not ground or ground['initial_overlap'] or ground['normal'][2]<.7:
            raise RuntimeError('Hovercraft perimeter exit lacks safe pier floor')
        foot=vec(ground['point_cm']); center=foot+unreal.Vector(0,0,state['half']+3)
        trace=unreal.SystemLibrary.capsule_trace_single_by_profile(state['game'],previous,center,
            radius,state['half'],'Pawn',False,[state['pawn']],unreal.DrawDebugTrace.NONE,True)
        hit=trace.to_tuple() if trace else None
        checks.append({'from_cm':previous.to_tuple(),'to_cm':center.to_tuple(),'floor':ground,
            'blocking_actor':hit[9].get_path_name() if hit and hit[0] and hit[9] else None})
        if hit and hit[0]:
            report['exit_route_clearance']=checks;write()
            raise RuntimeError('Hovercraft perimeter exit is blocked by '+str(checks[-1]['blocking_actor']))
        path.append(foot); previous=center
    report['exit_route_clearance']=checks;write()
    return path

def tick(delta):
    if state['busy']: return
    state['busy']=True
    try:
        wall=time.monotonic()
        if state['phase']=='exit':
            if wall>state['deadline']: unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if wall>state['deadline']: raise RuntimeError('Timeout in '+state['phase'])
        if state['phase']=='setup':
            game=unreal.EditorLevelLibrary.get_game_world()
            if not game: return
            pawn=unreal.GameplayStatics.get_player_pawn(game,0); pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pawn or not pc: return
            if not isinstance(pawn,unreal.CarnivalPlayerCharacter): raise RuntimeError('Wrong player class')
            cls=unreal.CarnivalBoat if entry['kind']=='boat' else unreal.CarnivalHovercraft
            found=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,cls) if a.get_actor_label()==label]
            if len(found)!=1: raise RuntimeError('Expected exactly one saved vehicle, found '+str(len(found)))
            state.update(game=game,pawn=pawn,pc=pc,vehicle=found[0],half=pawn.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height())
            unreal.GameplayStatics.set_game_paused(game,False); unreal.GameplayStatics.set_global_time_dilation(game,1.)
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0'); pc.set_ignore_move_input(False)
            approach=[vec(p) for p in entry['approach_world_cm']]; state['approach']=approach
            f=floor(approach[0],[pawn,state['vehicle']]); report['start_floor']=f
            if not f or f['initial_overlap'] or f['normal'][2]<.7 or abs(f['point_cm'][2]-approach[0].z)>60:
                raise RuntimeError('Surveyed starting floor missing')
            pawn.get_movement_component().stop_movement_immediately()
            pawn.set_actor_location(vec(f['point_cm'])+unreal.Vector(0,0,state['half']+3),False,True)
            state.update(phase='start_settle',ready=wall+1); write(); return
        pawn=state['pawn']; vehicle=state['vehicle']; pos=pawn.get_actor_location()
        if state['phase']=='start_settle' and wall>=state['ready']:
            if not check_ground(pos): raise RuntimeError('Initial pawn did not settle on safe ground')
            walk_begin(state['approach'][1:],'walk_to_board'); event('approach_started'); return
        if state['phase'] in ('walk_to_board','walk_back'):
            if pawn.get_movement_component().is_swimming(): raise RuntimeError('Dry approach entered swimming')
            target=state['path'][state['index']]; distance=xy(pos,target)
            segment_start=state['segment_start'];dx=target.x-segment_start.x;dy=target.y-segment_start.y
            fraction=max(0,min(1,((pos.x-segment_start.x)*dx+(pos.y-segment_start.y)*dy)/max(dx*dx+dy*dy,1)))
            expected_floor=segment_start.z+(target.z-segment_start.z)*fraction
            if pos.z<expected_floor+state['half']-100:
                raise RuntimeError('Approach fell below measured floor along the current segment')
            if wall-state['last_walk_sample']>.5:
                report.setdefault('walk_samples',[]).append({'phase':state['phase'],'pawn_cm':pos.to_tuple(),
                    'expected_floor_z_cm':expected_floor,'actual_floor':floor(pos,[pawn,vehicle]),
                    'movement_mode':str(pawn.get_movement_component().get_editor_property('movement_mode'))})
                state['last_walk_sample']=wall;write()
            # Boarding must reach the saved marker accurately. Stopping 55 cm
            # early can leave the capsule outside the actual mount trigger.
            tolerance=15 if state['phase']=='walk_to_board' and state['index']+1==len(state['path']) else 55
            if distance<tolerance:
                if state['index']+1<len(state['path']): state['segment_start']=target;state['index']+=1; return
                pawn.get_movement_component().stop_movement_immediately()
                state.update(phase='board_settle' if state['phase']=='walk_to_board' else 'finish_settle',ready=wall+.75); return
            if xy(pos,state['progress'])>15: state.update(progress=pos,progress_time=wall)
            elif wall-state['progress_time']>5: raise RuntimeError('Approach movement stalled')
            direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0)/distance
            state['pc'].set_control_rotation(unreal.Rotator(pitch=-10,yaw=math.degrees(math.atan2(direction.y,direction.x)),roll=0))
            pawn.add_movement_input(direction,1,True); return
        if state['phase']=='board_settle' and wall>=state['ready']:
            f=check_ground(pos)
            if not f: raise RuntimeError('Boarding approach is not grounded')
            seat=unreal.MathLibrary.transform_location(vehicle.get_actor_transform(),vehicle.get_editor_property('driver_relative_offset'))
            capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
            trace=unreal.SystemLibrary.capsule_trace_single_by_profile(state['game'],pos,seat,
                capsule.get_scaled_capsule_radius(),state['half'],'Pawn',False,[pawn,vehicle],unreal.DrawDebugTrace.NONE,True)
            hit=trace.to_tuple() if trace else None
            report['mount_diagnostics']={'pawn_cm':pos.to_tuple(),'vehicle_cm':vehicle.get_actor_location().to_tuple(),
                'seat_cm':seat.to_tuple(),'trigger_overlap':vehicle.get_editor_property('mount_trigger').is_overlapping_actor(pawn),
                'speed_cm_s':speed(),'seat_path_blocker':{'actor':hit[9].get_path_name() if hit[9] else None,
                    'component':hit[10].get_path_name() if hit[10] else None,'initial_overlap':bool(hit[1])} if hit and hit[0] else None}
            write()
            if not vehicle.can_mount(pawn): raise RuntimeError('Saved approach cannot reach vehicle seat')
            event('board_requested',pawn_cm=pos.to_tuple(),floor=f)
            pawn.try_interact_or_mount(); state.update(phase='board_check',ready=wall+.5); return
        if state['phase']=='board_check' and wall>=state['ready']:
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=vehicle or vehicle.get_editor_property('current_rider')!=pawn:
                raise RuntimeError('Context interaction did not mount this vehicle')
            origin=vehicle.get_actor_location(); yaw=vehicle.get_actor_rotation().yaw; a=math.radians(yaw)
            state.update(origin=origin,forward=unreal.Vector(math.cos(a),math.sin(a),0),yaw=yaw,phase='drive_outbound',deadline=wall+120,last_sample=0,progress_time=wall,progress=origin)
            event('mounted',vehicle_cm=origin.to_tuple()); return
        if state['phase'] in ('drive_outbound','drive_return'):
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=vehicle or vehicle.get_editor_property('current_rider')!=pawn: raise RuntimeError('Lost driver possession')
            vpos=vehicle.get_actor_location(); d=vpos-state['origin']; fwd=state['forward']
            along=d.x*fwd.x+d.y*fwd.y; lateral=abs(d.x*fwd.y-d.y*fwd.x)
            if lateral>float(entry.get('drive_lane_half_width_cm',300)): raise RuntimeError('Vehicle departed surveyed drive lane')
            if abs(d.z)>float(entry.get('drive_max_height_delta_cm',100 if entry['kind']=='boat' else 300)): raise RuntimeError('Vehicle left expected water/hover height')
            if xy(vpos,state['progress'])>15: state.update(progress=vpos,progress_time=wall)
            elif wall-state['progress_time']>8: raise RuntimeError('Vehicle stalled in drive lane')
            outward=state['phase']=='drive_outbound'; remaining=entry['drive_distance_cm']-along if outward else along
            sign=1 if outward else -1
            angle=(vehicle.get_actor_rotation().yaw-state['yaw']+180)%360-180
            # Boat rudder reverses with astern motion; hover yaw does not.
            steering_sign=sign if entry['kind']=='boat' else 1
            vehicle.input_steering(max(-.25,min(.25,-angle/30))*steering_sign)
            if remaining<55:
                vehicle.clear_control_inputs()
                if speed()<10:
                    event('outbound_stop' if outward else 'return_stop',vehicle_cm=vpos.to_tuple(),distance_cm=along,lateral_cm=lateral)
                    if outward: state.update(phase='drive_return',progress_time=wall,deadline=wall+120)
                    else: state.update(phase='unload',ready=wall+.75,deadline=wall+20)
            else: vehicle.input_throttle(sign*max(.07,min(.2,remaining/2000)))
            if wall-state['last_sample']>.5:
                report['samples'].append({'phase':state['phase'],'vehicle_cm':vpos.to_tuple(),'along_cm':along,'lateral_cm':lateral,'speed_cm_s':speed()})
                state['last_sample']=wall; write()
            return
        if state['phase']=='unload' and wall>=state['ready']:
            vehicle.dismount(); state.update(phase='unload_check',ready=wall+1); return
        if state['phase']=='unload_check' and wall>=state['ready']:
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=pawn or vehicle.get_editor_property('current_rider'):
                raise RuntimeError('Ordinary unloading failed at returned boarding location')
            f=check_ground(pos)
            if not f: raise RuntimeError('Unloaded pawn lacks safe floor')
            event('unloaded',pawn_cm=pos.to_tuple(),floor=f)
            walk_begin(return_path_after_unload(pos),'walk_back'); return
        if state['phase']=='finish_settle' and wall>=state['ready']:
            f=check_ground(pos)
            if not f: raise RuntimeError('Return approach is not grounded')
            event('walk_return_complete',pawn_cm=pos.to_tuple(),floor=f); finish()
    except Exception: finish(traceback.format_exc())
    finally: state['busy']=False

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
if not world: raise RuntimeError('Could not load main world')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_class().get_name()=='MetaHumanMassSpawner': report['excluded_spawners'].append(a.get_actor_label()); eas.destroy_actor(a)
handle=unreal.register_slate_post_tick_callback(tick); write(); le.editor_request_begin_play()
