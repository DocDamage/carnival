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
extended=os.environ.get('CARNIVAL_BOAT_EXTENDED_ROUTE')=='1'
boundary_probe=os.environ.get('CARNIVAL_BOAT_BOUNDARY_PROBE')=='1'
maneuver_probe=os.environ.get('CARNIVAL_BOAT_MANEUVER_PROBE')=='1'
activity_probe=os.environ.get('CARNIVAL_BOAT_ACTIVITY_PROBE')=='1'
extension=None
if maneuver_probe and (not extended or boundary_probe): raise RuntimeError('Maneuver probe needs extended route and no boundary probe')
if activity_probe and (not extended or maneuver_probe): raise RuntimeError('Course probe needs the extended straight boat route')
if boundary_probe and not extended: raise RuntimeError('Boundary probe requires the extended surveyed route')
if extended:
    if entry['kind']!='boat': raise RuntimeError('Extended route is boat-only')
    extension_path=OUT/('NorthDockBoatRoute_'+os.environ.get('CARNIVAL_BOAT_ROUTE_REVISION','20261029_v2'))/'index.json'
    extension=json.loads(extension_path.read_text())
    if not extension['success'] or extension['errors']: raise RuntimeError('Extended route authoring failed')
    level=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout.umap'
    if hashlib.sha256(level.read_bytes()).hexdigest()!=extension['after'][level.name]: raise RuntimeError('Extended route level changed after authoring')
    entry=extension['route_entry']
report_name=label+('_Course_20261029' if activity_probe else '_Maneuvers_20261029' if maneuver_probe else '_Boundary_20261029' if boundary_probe else '_ExtendedRoute_20261029' if extended else '_Lifecycle')+'.json'
report_name=os.environ.get('CARNIVAL_WATER_VEHICLE_REPORT',report_name)
if Path(report_name).name!=report_name or not report_name.endswith('.json'): raise ValueError('Use a report filename only')
# Clearance evidence is required separately from the boarding/water-plane probe.
if not entry.get('drive_lane_survey_evidence') or entry.get('drive_distance_cm',0)<1000:
    raise RuntimeError('Plan needs a measured clear drive lane of at least 10 m')
if not label.replace('_','').isalnum(): raise ValueError('Unsafe report label')
report={'success':False,'vehicle':label,'kind':entry['kind'],'plan_sha256':digest,
        'errors':[],'samples':[],'events':[],'excluded_spawners':[],
        'scope':'Real saved vehicle: walk approach, contextual mount, powered outbound, continuous reverse return, ordinary safe unload and walk back.',
        'limits':'Direct movement/control APIs, no physical gamepad. This short clearance lane does not accept an entire activity course, all water boundaries, rendered presentation or performance.'}
if extended:
    report.update(extension_sha256=hashlib.sha256(extension_path.read_bytes()).hexdigest(),boundary_probe=boundary_probe,maneuver_probe=maneuver_probe,
        limits='Scripted normal-speed straight journey, boarding/unloading and optional southern-boundary stop/reverse. Turning, other boundaries, activity scoring, physical controls and rendering remain open.')
if maneuver_probe:
    report.update(scope='Normal-speed contextual boarding, six forward/reverse steering arcs, return and sideways parking, ordinary unload and walk back.',
        limits='Scripted controls with crowd excluded. Accepts this maneuver sequence and return to berth; other boundaries, activity scoring, physical controls, rendering and performance remain open.')
if activity_probe:
    report.update(scope='Contextual course start, walk/board/drive/return/unload, checkpoint scoring, reset, replay and cancellation.',
        limits='Scripted normal-speed controls with crowd excluded; rendering, physical controls and other boundaries remain open.')
OUT.mkdir(parents=True,exist_ok=True)
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
state={'phase':'setup','deadline':time.monotonic()+240,'busy':False}

def vec(p): return unreal.Vector(*[float(x) for x in p])
def xy(a,b): return math.hypot(a.x-b.x,a.y-b.y)
def write():
    report['phase']=state['phase']; report['timestamp']=time.time()
    pending=OUT/(report_name+'.tmp');pending.write_text(json.dumps(report,indent=2));pending.replace(OUT/report_name)
def event(name,**details):
    report['events'].append({'name':name,'seconds':unreal.GameplayStatics.get_time_seconds(state['game']),**details}); write()

def begin_maneuver_step():
    pos=state['vehicle'].get_actor_location()
    if state['maneuver_index']>=len(state['maneuvers']):
        if not state.get('shift_planned'):
            state['shift_planned']=True
            dx=state['origin'].x-pos.x
            # Opposite steering arcs translate the boat sideways while ending
            # on its original heading. Radius is measured from the first arc.
            if abs(dx)>30:
                radius=state['turn_radius']
                if abs(dx)>radius: raise RuntimeError('Turn drift exceeds the parking maneuver envelope')
                alpha=math.degrees(math.acos(1-abs(dx)/(2*radius)))
                state['maneuvers'].extend([('arc',state['yaw']+math.copysign(alpha,dx),1),
                                          ('arc',state['yaw'],1),('home_y',None,-1)])
                report['parking_shift_cm']=dx;report['parking_arc_degrees']=alpha
        if state['maneuver_index']>=len(state['maneuvers']):
            offset=xy(pos,state['origin'])
            if offset>90: raise RuntimeError('Maneuvers did not return to the boarding pose: '+str(offset))
            report['maneuver_return_offset_cm']=offset
            event('maneuvers_returned',vehicle_cm=pos.to_tuple(),offset_cm=offset)
            state.update(phase='unload',ready=time.monotonic()+.75,deadline=time.monotonic()+20)
            return
    state.update(phase='maneuver',maneuver_start=pos,progress=pos,
                 progress_game=unreal.GameplayStatics.get_time_seconds(state['game']),deadline=time.monotonic()+120)
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
    report['success']=not report['errors'] and (not activity_probe or (report.get('course_completed_and_reset') and report.get('course_replay_and_abort'))); write(); le.editor_request_end_play()
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
            if activity_probe:
                state['activity']=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalActivityBase)
                    if a.get_actor_label()==label+'_HandlingActivity')
            if extended:
                vehicle=state['vehicle']
                report['saved_bounds']=[vehicle.get_editor_property('navigable_water_min').to_tuple(),vehicle.get_editor_property('navigable_water_max').to_tuple()]
                if not vehicle.get_editor_property('use_navigable_water_bounds') or any(abs(a-b)>.1 for a,b in zip(report['saved_bounds'][0]+report['saved_bounds'][1],entry['navigable_water_min_world_cm']+entry['navigable_water_max_world_cm'])):
                    raise RuntimeError('Saved boat navigation bounds do not match route authoring')
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
            if activity_probe and pawn.get_editor_property('nearby_activity')==state['activity']:
                activity=state['activity']
                if state['phase']=='walk_to_board' and not state.get('course_started'):
                    pawn.try_context_interact()
                    if activity.get_editor_property('activity_state')!=unreal.CarnivalActivityState.ACTIVE: raise RuntimeError('Context did not start boat activity')
                    state['course_started']=True;event('course_started_through_context')
                elif state['phase']=='walk_back' and not report.get('course_replay_and_abort'):
                    pawn.try_context_interact()
                    if activity.get_editor_property('activity_state')!=unreal.CarnivalActivityState.ACTIVE: raise RuntimeError('Boat course replay failed')
                    if activity.get_editor_property('current_score')!=0 or activity.get_editor_property('current_checkpoint_index')!=0: raise RuntimeError('Replay did not reset boat course progress')
                    activity.abort_activity()
                    if activity.get_editor_property('activity_state')!=unreal.CarnivalActivityState.INACTIVE or pawn.get_editor_property('active_activity'): raise RuntimeError('Boat cancellation did not clear activity')
                    report['course_replay_and_abort']=True;event('course_replayed_and_aborted')
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
            if activity_probe and not state.get('course_started'): raise RuntimeError('Never reached boat course start trigger')
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
            event('mounted',vehicle_cm=origin.to_tuple())
            if maneuver_probe:
                if abs((yaw+90+180)%360-180)>1: raise RuntimeError('Maneuver plan expects the saved south-facing berth')
                state.update(maneuvers=[('arc',0,1),('arc',60,-1),('arc',120,1),('arc',180,-1),
                                        ('arc',240,1),('arc',270,-1),('home_y',None,-1)],maneuver_index=0)
                begin_maneuver_step()
            return
        if state['phase'] in ('maneuver','maneuver_brake'):
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=vehicle or vehicle.get_editor_property('current_rider')!=pawn: raise RuntimeError('Lost driver during maneuver')
            vpos=vehicle.get_actor_location();rot=vehicle.get_actor_rotation()
            if not vehicle.is_water_transform_navigable(vpos,rot): raise RuntimeError('Maneuver hull left navigable water')
            gt=unreal.GameplayStatics.get_time_seconds(state['game'])
            if xy(vpos,state['progress'])>15: state.update(progress=vpos,progress_game=gt)
            elif gt-state['progress_game']>8: raise RuntimeError('Maneuver stalled at '+str(vpos.to_tuple()))
            kind,target,direction=state['maneuvers'][state['maneuver_index']]
            if state['phase']=='maneuver_brake':
                vehicle.clear_control_inputs()
                if speed()<5:
                    event('maneuver_step',index=state['maneuver_index'],kind=kind,target_yaw=target,
                          actual_yaw=rot.yaw,vehicle_cm=vpos.to_tuple())
                    if state['maneuver_index']==0:
                        delta=vpos-state['maneuver_start'];state['turn_radius']=(abs(delta.x)+abs(delta.y))/2
                        report['measured_turn_radius_cm']=state['turn_radius']
                    state['maneuver_index']+=1;begin_maneuver_step()
                return
            error=((target if kind=='arc' else state['yaw'])-rot.yaw+180)%360-180
            arrived=abs(error)<.35 if kind=='arc' else state['origin'].y-vpos.y<25
            if arrived:
                vehicle.clear_control_inputs();state['phase']='maneuver_brake';return
            # Equal low forward/reverse speed yields the same physical arc
            # radius; rudder direction reverses when moving astern.
            vehicle.input_throttle(.07 if direction>0 else -.1925)
            vehicle.input_steering(math.copysign(1,error)*direction if kind=='arc' else max(-.2,min(.2,error/20))*direction)
            if wall-state['last_sample']>.5:
                report['samples'].append({'phase':'maneuver','index':state['maneuver_index'],'kind':kind,
                    'vehicle_cm':vpos.to_tuple(),'yaw':rot.yaw,'speed_cm_s':speed()})
                state['last_sample']=wall;write()
            return
        if state['phase']=='boundary_push':
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=vehicle or vehicle.get_editor_property('current_rider')!=pawn: raise RuntimeError('Lost driver at boundary')
            vpos=vehicle.get_actor_location();rot=vehicle.get_actor_rotation()
            if not vehicle.is_water_transform_navigable(vpos,rot): raise RuntimeError('Hull crossed surveyed boundary or keel clearance')
            vehicle.input_throttle(.2);vehicle.input_steering(0)
            blocked=not vehicle.is_water_transform_navigable(vpos+state['forward']*50,rot)
            if xy(vpos,state['boundary_last'])>3:
                state.update(boundary_last=vpos,boundary_stable=wall)
            if blocked and speed()<1 and wall-state['boundary_stable']>.75 and wall-state['boundary_started']>1.5:
                event('southern_boundary_held',vehicle_cm=vpos.to_tuple(),speed_cm_s=speed(),forward_50cm_rejected=blocked,
                    hull_inside=vehicle.is_water_transform_navigable(vpos,rot))
                report['boundary_stop_verified']=True;vehicle.clear_control_inputs()
                state.update(phase='drive_return',progress_time=wall,deadline=wall+120,progress=vpos)
            if wall-state['last_sample']>.5:
                report['samples'].append({'phase':'boundary_push','vehicle_cm':vpos.to_tuple(),'speed_cm_s':speed(),'forward_50cm_rejected':blocked})
                state['last_sample']=wall;write()
            return
        if state['phase'] in ('drive_outbound','drive_return'):
            if unreal.GameplayStatics.get_player_pawn(state['game'],0)!=vehicle or vehicle.get_editor_property('current_rider')!=pawn: raise RuntimeError('Lost driver possession')
            vpos=vehicle.get_actor_location(); d=vpos-state['origin']; fwd=state['forward']
            if extended and not vehicle.is_water_transform_navigable(vpos,vehicle.get_actor_rotation()): raise RuntimeError('Hull left navigable water during journey')
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
                    if outward and boundary_probe:
                        state.update(phase='boundary_push',boundary_started=wall,boundary_stable=wall,boundary_last=vpos,
                                     deadline=wall+30)
                    elif outward: state.update(phase='drive_return',progress_time=wall,deadline=wall+120)
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
            if activity_probe:
                activity=state['activity']
                if activity.get_editor_property('activity_state')!=unreal.CarnivalActivityState.COMPLETED or activity.get_editor_property('current_checkpoint_index')!=2 or activity.get_editor_property('current_score')!=200: raise RuntimeError('Boat course did not complete both checkpoints')
                event('course_completed',score=activity.get_editor_property('current_score'),elapsed_seconds=activity.get_editor_property('elapsed_time'))
                pawn.try_context_interact()
                if activity.get_editor_property('activity_state')!=unreal.CarnivalActivityState.INACTIVE or pawn.get_editor_property('active_activity'): raise RuntimeError('Boat completion reset failed')
                report['course_completed_and_reset']=True
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
