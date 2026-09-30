"""Integrated pawn round trips and real camera/dry-route checks, without map edits.

Run with run_doll_tool.py playtest (geometry) or render-pie (optional images).
CARNIVAL_INTERIOR_CASES is a comma list; CARNIVAL_INTERIOR_CAPTURE=1 captures
the actual player view at both ends. Never rotates door leaves or enables flight.
"""
import hashlib,json,math,os,sys,time,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/InteriorCameraAcceptance'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'Scripts'))
from industrial_hospital_route_config import HOSPITAL_YAW,hospital_level_transform
MAIN='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
CAPTURE=os.environ.get('CARNIVAL_INTERIOR_CAPTURE')=='1'
REPORT_NAME=os.environ.get('CARNIVAL_INTERIOR_REPORT','Roundtrips')
if not REPORT_NAME.replace('_','').isalnum(): raise ValueError('Unsafe report name')
report={'success':False,'map':MAIN,'started_epoch':time.time(),'movement':'Actual Carnival pawn, normal time, continuous return; only initial position per independent case is teleported.',
        'camera':'Actual PlayerCameraManager positions after controller look; geometry checks use the Camera channel.',
        'limits':'No physical input, no full room inventory acceptance, no shore/swimming/recovery acceptance. Screenshots require separate visual review.',
        'capture_requested':CAPTURE,'cases':[],'errors':[],'source_hashes':{},'excluded_spawners':[]}
for name in ('L_HauntedMansionConnected','L_IndustrialHospitalInteriorArchitecture','L_IndustrialHospitalSetDress',
             'L_CarnivalWorldExpansion_Sewers','L_CarnivalWorldExpansion_Atlantis','L_CarnivalWorldExpansion_Connections_Layout'):
    path=ROOT/'Content/Carnival/World/Levels'/(name+'.umap')
    if path.exists(): report['source_hashes'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()

def load_guide(name):
    path=ROOT/'Saved/MansionConnection'/('RoomWalk_PIE_'+name+'.json')
    report['source_hashes'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    data=json.loads(path.read_text())
    if not data.get('success') or not data.get('planned_waypoints'): raise RuntimeError('Missing successful guide '+name)
    # Prior room guide Z is capsule center; derive intended floor from its own recorded capsule size.
    height=float(data.get('capsule_half_height_cm',98.2))
    return [[p[0],p[1],p[2]-height] for p in data['planned_waypoints']]

def hospital_points():
    origin=hospital_level_transform(); a=math.radians(HOSPITAL_YAW)
    return [(origin[0]+x*math.cos(a)-y*math.sin(a),origin[1]+x*math.sin(a)+y*math.cos(a),origin[2]+80)
            for x,y in [(5200,-2300),(5200,-1000),(5000,-850),(5000,-350),(5200,-200)]]

selected=os.environ.get('CARNIVAL_INTERIOR_CASES','mansion_mission_rooms,hospital_entrance,sewer_corridor,atlantis_hall').split(',')
routes={
    'hospital_entrance':hospital_points(),
    'sewer_corridor':[(-27000,-12500,-1800),(-27100,-12000,-1800),(-27100,-9654,-1800)],
    # R12's carved opening exposes its 35 cm-thick walkway: center -1800,
    # upper face approximately -1782.5, not the removed hall slab top -1750.
    'atlantis_hall':[(-19000,-11000,-1750),(-18500,-11600,-1750),(-7500,-11600,-1750),(-7000,-11000,-1782.5)],
}
if 'mansion_mission_rooms' in selected:
    first=load_guide('foyer92_to_study_full_path'); second=load_guide('study_to_music_path')
    routes['mansion_mission_rooms']=first+second[1:]
if any(name.startswith('hospital_corridor_') for name in selected):
    candidate_path=ROOT/'Saved/IndustrialHospital/Hospital_Candidate_Routes.json'
    report['source_hashes'][str(candidate_path)]=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    candidates=json.loads(candidate_path.read_text())
    for name,item in candidates['routes'].items(): routes[name]=item['candidate_floor_points_cm']
if any(name in selected for name in ('sewer_stair_handoff','sewer_lower_corridor')):
    candidate_path=ROOT/'Saved/WorldExpansion/Sewer_Handoff_Fine_Candidate.json'
    candidate=json.loads(candidate_path.read_text())
    if not candidate.get('success') or 'sewer_stair_handoff' in selected and not candidate.get('route_found'):
        raise RuntimeError('Sewer handoff requires a fresh measured candidate path')
    for name,digest in candidate['source_hashes'].items():
        actual=ROOT/'Content/Carnival/World/Levels'/(name+'.umap')
        if hashlib.sha256(actual.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Sewer candidate uses stale level geometry '+name)
    report['source_hashes'][str(candidate_path)]=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    if 'sewer_stair_handoff' in selected:routes['sewer_stair_handoff']=candidate['candidate_floor_points_cm']
    if 'sewer_lower_corridor' in selected:
        routes['sewer_lower_corridor']=candidate['partial_floor_points_cm']
        report['partial_sewer_scope']=candidate['partial_scope']
        report['remaining_R11_handoff_gap_cm']=candidate['partial_remaining_handoff_gap_cm']
if any(name not in routes for name in selected): raise ValueError('Unknown case: '+','.join(selected))
report['candidate_only_routes']=['sewer_corridor','atlantis_hall']+[name for name in selected if name.startswith('hospital_corridor_')]
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
state={'phase':'setup','deadline':time.monotonic()+240,'busy':False,'case_index':0}

def write():
    report['heartbeat']={'phase':state['phase'],'time':time.time(),'case_index':state['case_index']}
    (OUT/(REPORT_NAME+'.json')).write_text(json.dumps(report,indent=2))

def vec(v): return unreal.Vector(*[float(x) for x in v])
def xy(a,b): return math.hypot(a.x-b.x,a.y-b.y)
def hit_row(hit):
    h=hit.to_tuple() if hit else None
    if not h or not h[0]: return None
    return {'actor':h[9].get_actor_label() if h[9] else None,'path':h[9].get_path_name() if h[9] else None,
            'point_cm':h[5].to_tuple(),'normal':h[7].to_tuple(),'initial_overlap':bool(h[1])}

def floor_at(point):
    return hit_row(unreal.SystemLibrary.line_trace_single(state['game'],point+unreal.Vector(0,0,100),point-unreal.Vector(0,0,260),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,[state['pawn']],unreal.DrawDebugTrace.NONE,True))

def next_case(error=None):
    if error:
        report['errors'].append(selected[state['case_index']]+': '+error)
        if state.get('current'): state['current']['error']=error
    state['pawn'].get_movement_component().stop_movement_immediately()
    state['case_index']+=1
    if state['case_index']>=len(selected):
        report['success']=not report['errors'] and all(c.get('success') for c in report['cases'])
        report['finished_epoch']=time.time(); write(); le.editor_request_end_play()
        state.update(phase='exit',deadline=time.monotonic()+3)
    else: begin_case()

def begin_case():
    name=selected[state['case_index']]; path=[vec(p) for p in routes[name]]
    current={'name':name,'success':False,'path_floor_cm':[p.to_tuple() for p in path],'legs':[],'camera_checks':[],'captures':[]}
    report['cases'].append(current); state.update(current=current,path=path,reverse=False,index=1)
    if name=='sewer_corridor':
        current['handoff_floor_probes']=[]
        for x in (-27200,-27100,-27000):
            for y in (-12700,-12500,-12300,-12000,-11500,-10000,-9654):
                for top in (-1700,-1600,-1500,-1400):
                    h=hit_row(unreal.SystemLibrary.line_trace_single(state['game'],unreal.Vector(x,y,top),unreal.Vector(x,y,-2200),
                        unreal.TraceTypeQuery.ECC_VISIBILITY,False,[state['pawn']],unreal.DrawDebugTrace.NONE,True))
                    current['handoff_floor_probes'].append({'start_cm':[x,y,top],'hit':h})
    floor=floor_at(path[0])
    current['start_floor']=floor
    if not floor: next_case('No start floor at intended elevation'); return
    start=vec(floor['point_cm'])+unreal.Vector(0,0,state['half_height']+3)
    if abs(start.z-(path[0].z+state['half_height']))>90: next_case('Start is on wrong floor'); return
    state['pawn'].get_movement_component().stop_movement_immediately()
    if not state['pawn'].set_actor_location(start,False,True): next_case('Initial positioning failed'); return
    state.update(phase='settle',ready=time.monotonic()+1,deadline=time.monotonic()+45)
    write()

def begin_leg(reverse):
    if reverse: state['path']=list(reversed(state['path']))
    now=unreal.GameplayStatics.get_time_seconds(state['game']); pos=state['pawn'].get_actor_location()
    state.update(phase='walk',reverse=reverse,index=1,leg_start=now,progress_time=now,progress_position=pos,last_sample=now-1,deadline=time.monotonic()+240)
    leg={'direction':'return' if reverse else 'outbound','success':False,'samples':[]}
    state['current']['legs'].append(leg); state['leg']=leg; write()

def begin_camera():
    state['pawn'].get_movement_component().stop_movement_immediately()
    direction=state['path'][-1]-state['path'][-2]
    yaw=math.degrees(math.atan2(direction.y,direction.x))
    state.update(phase='camera_turn',views=[(-10,yaw+x) for x in (0,90,180,270)]+[(35,yaw),(-35,yaw)],view_index=0,deadline=time.monotonic()+60)

def tick(delta):
    if state['busy']: return
    state['busy']=True
    try:
        wall=time.monotonic()
        if state['phase']=='exit':
            if wall>=state['deadline']: unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if wall>state['deadline']:
            if state.get('pawn'): next_case('Wall clock timeout in '+state['phase'])
            else:
                report['errors'].append('PIE pawn setup timed out'); write(); le.editor_request_end_play(); state.update(phase='exit',deadline=wall+3)
            return
        if state['phase']=='setup':
            game=unreal.EditorLevelLibrary.get_game_world()
            if not game: return
            pawn=unreal.GameplayStatics.get_player_pawn(game,0); pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pawn or not pc: return
            if not isinstance(pawn,unreal.CarnivalPlayerCharacter): raise RuntimeError('Expected Carnival gameplay pawn')
            unreal.GameplayStatics.set_game_paused(game,False); unreal.GameplayStatics.set_global_time_dilation(game,1.)
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0'); pc.set_ignore_move_input(False)
            capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
            state.update(game=game,pawn=pawn,pc=pc,half_height=capsule.get_scaled_capsule_half_height(),radius=capsule.get_scaled_capsule_radius())
            report['player_class']=pawn.get_class().get_name(); report['capsule_half_height_cm']=state['half_height']
            begin_case(); return
        pawn=state['pawn']; pos=pawn.get_actor_location(); move=pawn.get_movement_component()
        if state['phase']=='settle':
            if wall>=state['ready']: begin_leg(False)
            return
        if move.is_swimming(): next_case('Dry interior route entered swimming mode'); return
        if state['phase']=='walk':
            now=unreal.GameplayStatics.get_time_seconds(state['game']); path=state['path']; target=path[state['index']]
            remaining=xy(pos,target)
            if pos.z<target.z-120: next_case('Pawn fell below intended floor'); return
            if xy(pos,state['progress_position'])>15:
                state.update(progress_position=pos,progress_time=now)
            elif now-state['progress_time']>4:
                obstruction=hit_row(unreal.SystemLibrary.capsule_trace_single(state['game'],pos,unreal.Vector(target.x,target.y,pos.z),
                    state['radius'],state['half_height'],unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True))
                state['leg']['blocker']=obstruction; state['leg']['stuck_cm']=pos.to_tuple(); next_case('No movement progress for 4 game seconds'); return
            if now-state['last_sample']>=.5:
                state['leg']['samples'].append({'seconds':round(now-state['leg_start'],2),'position_cm':pos.to_tuple(),'mode':str(move.get_editor_property('movement_mode')),'camera_cm':unreal.GameplayStatics.get_player_camera_manager(state['game'],0).get_camera_location().to_tuple()})
                state['last_sample']=now; write()
            tolerance=65
            if selected[state['case_index']] in ('sewer_stair_handoff','sewer_lower_corridor'):
                segment=xy(path[state['index']-1],target)
                tolerance=max(8,min(25,segment*.25))
            if remaining<tolerance:
                if state['index']<len(path)-1: state['index']+=1; return
                pawn.get_movement_component().stop_movement_immediately()
                state.update(phase='endpoint_settle',ready=wall+.75,deadline=wall+10); return
            direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0)/max(remaining,1)
            state['pc'].set_control_rotation(unreal.Rotator(pitch=-10,yaw=math.degrees(math.atan2(direction.y,direction.x)),roll=0))
            scale=max(.15,min(1,remaining/60)) if selected[state['case_index']] in ('sewer_stair_handoff','sewer_lower_corridor') else 1
            # Tight surveyed corners need the same analogue slowing available
            # to a player; full-speed overshoot can cut outside a clear path.
            pawn.add_movement_input(direction,scale,True)
        elif state['phase']=='endpoint_settle' and wall>=state['ready']:
            target=state['path'][-1]; floor=floor_at(target)
            state['leg']['endpoint_floor_probe']=floor
            state['leg']['endpoint_position_cm']=pos.to_tuple()
            if not floor or floor['initial_overlap'] or floor['normal'][2]<.7 or not move.is_moving_on_ground() or abs(pos.z-vec(floor['point_cm']).z-state['half_height'])>45 or abs(pos.z-(target.z+state['half_height']))>90:
                next_case('Endpoint height/floor mismatch after settling'); return
            now=unreal.GameplayStatics.get_time_seconds(state['game'])
            state['leg'].update(success=True,seconds=round(now-state['leg_start'],2),finish_cm=pos.to_tuple(),floor=floor)
            begin_camera(); write(); return
        elif state['phase']=='camera_turn':
            pitch,yaw=state['views'][state['view_index']]
            state['pc'].set_control_rotation(unreal.Rotator(pitch=pitch,yaw=yaw,roll=0))
            state.update(phase='camera_sample',ready=wall+.4)
        elif state['phase']=='camera_sample' and wall>=state['ready']:
            manager=unreal.GameplayStatics.get_player_camera_manager(state['game'],0); camera=manager.get_camera_location()
            camera_hit=hit_row(unreal.SystemLibrary.sphere_trace_single(state['game'],camera,camera+unreal.Vector(.1,0,0),4,
                unreal.TraceTypeQuery.ECC_CAMERA,False,[pawn],unreal.DrawDebugTrace.NONE,True))
            row={'direction':'return' if state['reverse'] else 'outbound','pitch_yaw':state['views'][state['view_index']],
                 'pawn_cm':pos.to_tuple(),'camera_cm':camera.to_tuple(),'camera_overlap':camera_hit}
            state['current']['camera_checks'].append(row)
            if camera_hit: report['errors'].append(selected[state['case_index']]+': camera sphere overlaps '+str(camera_hit['actor']))
            if CAPTURE and state['view_index']==0:
                path=OUT/(REPORT_NAME+'_'+selected[state['case_index']]+'_'+row['direction']+'.png')
                unreal.SystemLibrary.execute_console_command(state['game'],'HighResShot 1280x800 filename="'+path.as_posix()+'"')
                state.update(phase='capture',capture_path=path,capture_epoch=time.time(),deadline=wall+30)
            else: advance_view()
            write()
        elif state['phase']=='capture':
            path=state['capture_path']
            if path.exists() and path.stat().st_mtime>=state['capture_epoch']-1 and path.stat().st_size>10000:
                state['current']['captures'].append(str(path)); advance_view()
    except Exception:
        error=traceback.format_exc()
        if state.get('pawn') and state['case_index']<len(selected): next_case(error)
        else:
            report['errors'].append(error); write(); le.editor_request_end_play(); state.update(phase='exit',deadline=time.monotonic()+3)
    finally: state['busy']=False

def advance_view():
    state['view_index']+=1
    if state['view_index']<len(state['views']): state.update(phase='camera_turn',deadline=time.monotonic()+60)
    elif not state['reverse']: begin_leg(True)
    else:
        state['current']['success']=all(x['success'] for x in state['current']['legs']) and not any(x['camera_overlap'] for x in state['current']['camera_checks'])
        next_case()

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
if not world: raise RuntimeError('Could not load integrated map')
for actor in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner':
        report['excluded_spawners'].append(actor.get_actor_label()); unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
handle=unreal.register_slate_post_tick_callback(tick)
state['deadline']=time.monotonic()+240; write(); le.editor_request_begin_play()
