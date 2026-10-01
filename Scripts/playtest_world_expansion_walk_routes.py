"""Exercise the integrated expansion routes with the project gameplay pawn in PIE."""
import hashlib, json, math, os, time, traceback
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival")
MAIN="/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT=ROOT/"Saved/WorldExpansion"
REGION=json.loads((OUT/"Region_Authoring.json").read_text(encoding="utf-8"))
CONNECTIONS={x["id"]:x for x in REGION["connections"]}

def catmull(controls, step=800.0):
    p=[]
    for i in range(len(controls)-1):
        a,b=controls[max(i-1,0)],controls[i]; d,e=controls[i+1],controls[min(i+2,len(controls)-1)]
        n=max(2,int(math.ceil(math.dist(b,d)/step)))
        for j in range(n):
            t=j/float(n); t2=t*t; t3=t2*t
            p.append(tuple(.5*(2*b[k]+(-a[k]+d[k])*t+(2*a[k]-5*b[k]+4*d[k]-e[k])*t2+(-a[k]+3*b[k]-3*d[k]+e[k])*t3) for k in range(3)))
    p.append(tuple(controls[-1])); return p

def resample(source, spacing=650.0):
    out=[source[0]]
    for a,b in zip(source,source[1:]):
        n=max(1,int(math.ceil(math.dist(a,b)/spacing)))
        for j in range(1,n+1):
            t=j/float(n); out.append(tuple(a[k]*(1-t)+b[k]*t for k in range(3)))
    return out

outer_controls=REGION.get("outer_route_spine",{}).get("controls_cm") or CONNECTIONS["R03"]["route"].get("spine_controls_cm")
# Optional per-control overrides, e.g. the Prison junction must pass the 2.9 m gap between
# SM_WallEntry and SM_WallEntryInt rather than the outer wall's end column at its pivot.
_overrides={"-30000,-25000":[-30158,-24842,600]}  # verified gap: OuterSpineGateGap_Walk_20261001
_overrides.update(json.loads(os.environ.get("CARNIVAL_SPINE_CONTROL_OVERRIDES","{}")))
outer_controls=[list(_overrides.get(f"{c[0]:.0f},{c[1]:.0f}",c)) for c in outer_controls]
outer=resample(catmull(outer_controls))
def drop_overshoot_lobes(points):
    """Remove Catmull overshoot lobes (a >120-degree hairpin); the world corner is a flat slab (SpineHairpinFix_20261001)."""
    i=1
    while i<len(points)-1:
        a,b,c=points[i-1],points[i],points[i+1]
        turn=abs((math.degrees(math.atan2(c[1]-b[1],c[0]-b[0])-math.atan2(b[1]-a[1],b[0]-a[0]))+180)%360-180)
        if turn>120: points=points[:max(i-2,1)]+points[i+2:]; i=max(i-3,1); continue
        i+=1
    return points
outer=drop_overshoot_lobes(outer)
lab=resample(catmull(CONNECTIONS["R09"]["route"]["controls_cm"]))
service=resample(catmull(CONNECTIONS["R10"]["route"]["controls_cm"]))
stair=CONNECTIONS["R10"]["stair"]
stairs=[tuple(stair["start_cm"][k]*(1-i/stair["step_count"])+stair["end_cm"][k]*(i/stair["step_count"]) for k in range(3)) for i in range(stair["step_count"]+1)]
CASES=[("lab_branch_prison_to_lab",lab),
       ("R10_surface",service), ("R10_stairs",stairs),
       # R12 is a swim down the Atlantis floor shaft since the wreck was sunk; playtest_shipwreck_dive.py covers it.
       *[(cid+"_tunnel",resample([CONNECTIONS[cid]["route"]["start_cm"],CONNECTIONS[cid]["route"]["end_cm"]],150.)) for cid in ("R11",)],
       ("outer_surface_mansion_to_hospital",outer)]
selected=os.environ.get("CARNIVAL_EXPANSION_CASES","")
if selected:
    names=selected.split(",")
    if set(names)-{name for name,_ in CASES}: raise ValueError("Unknown route case: "+selected)
    CASES=[case for case in CASES if case[0] in names]
prefix=os.environ.get("CARNIVAL_EXPANSION_REPORT","Walk_Route_Playtest")
time_dilation=float(os.environ.get('CARNIVAL_ROUTE_TIME_DILATION','1'))
if not 1. <= time_dilation <= 4.: raise ValueError('Time dilation must be between 1 and 4')
REPORT=OUT/(prefix+".json")
LIVE=OUT/(prefix+"_Live.json")
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report={"success":False,"map":MAIN,"movement":"CarnivalPlayerCharacter add_movement_input in PIE; rendering depends on launch mode; no physical input","time_dilation":1.0,"tests":[],"errors":[],"route_lengths_m":{name:sum(math.dist(a,b) for a,b in zip(path,path[1:]))/100. for name,path in CASES},"excluded_editor_only_spawners":[],"started_epoch":time.time(),"region_authoring_sha256":hashlib.sha256((OUT/"Region_Authoring.json").read_bytes()).hexdigest()}
report['time_dilation']=time_dilation
state={"phase":"startup","busy":False,"deadline":time.monotonic()+300,"setup_polls":0,"callback_count":0,"last_heartbeat":0.0,"last_wall_progress":None,"last_motion_position":None}
def save():
    heartbeat={"callback_count":state.get("callback_count",0),"last_tick_epoch":state.get("last_tick_epoch"),"last_game_time_seconds":state.get("last_game_time_seconds"),"world_paused":state.get("world_paused"),"player_position_cm":state.get("last_player_position_cm"),"player_velocity_cm_s":state.get("last_player_velocity_cm_s")}
    report["runner_heartbeat"]=heartbeat
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    payload={"phase":state["phase"],"polls":state.get("setup_polls"),"time":time.time(),"report":report,"runner_heartbeat":heartbeat}
    if state.get("player"): payload["player_position_cm"]=state["player"].get_actor_location().to_tuple()
    LIVE.write_text(json.dumps(payload,indent=2),encoding="utf-8")
def dist(a,b): return math.hypot(a.x-b.x,a.y-b.y)
def start_leg(reverse=False, teleport=False):
    vals=list(CASES[state["case_index"]][1])
    if reverse: vals.reverse()
    player=state["player"]; player.get_movement_component().stop_movement_immediately()
    if teleport:
        a,b=vals[0],vals[1]; yaw=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        report["teleport_succeeded"]=bool(player.set_actor_location(unreal.Vector(a[0],a[1],a[2]+150.0),False,True))
        player.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),True)
    now=unreal.GameplayStatics.get_time_seconds(state["game"])
    label=CASES[state["case_index"]][0]+("_return" if reverse else "_outbound")
    pos=player.get_actor_location()
    state.update(phase=label,reverse=reverse,route=[unreal.Vector(*x) for x in vals],index=1,last_index=0,last_progress=now,start=now,deadline=time.monotonic()+900,last_wall_progress=time.monotonic(),last_motion_position=pos)
    report["tests"].append({"name":label,"success":False,"start_cm":vals[0],"end_cm":vals[-1],"samples":[]}); save()
def finish(error=None):
    if error:
        if state.get('player') and state.get('route'):
            player=state['player']; pos=player.get_actor_location()
            target=state['route'][min(state.get('index',0),len(state['route'])-1)]
            direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0).normal()
            hit=unreal.SystemLibrary.capsule_trace_single(state['game'],pos,pos+direction*150,
                42,90,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[player],unreal.DrawDebugTrace.NONE,True)
            data=hit.to_tuple() if hit else None
            if data and data[0]:
                report.setdefault('failure_blockers',[]).append({'phase':state['phase'],
                    'actor':data[9].get_path_name() if data[9] else None,
                    'impact':data[5].to_tuple(),'normal':data[7].to_tuple()})
        report["errors"].append(state["phase"]+": "+error)
        if report["tests"]:
            report["tests"][-1]["error"]=error
            report["tests"][-1]["failure_position_cm"]=state.get("last_player_position_cm")
        if state.get("case_index",len(CASES)) < len(CASES)-1:
            state["case_index"]+=1
            start_leg(False,True)
            return
    report["finish_reason"]=error or ("Configured route set completed" if report.get("success") else "Stopped without a success flag")
    report["finish_epoch"]=time.time()
    unreal.log("WORLD_EXPANSION_ROUTE_FINISH "+str(report["finish_reason"]))
    report["phase"]=state["phase"]; report["last_index"]=state.get("index"); save()
    le.editor_request_end_play(); state.update(phase="exit",deadline=time.monotonic()+3)
def tick(delta):
    if state["busy"]: return
    state["busy"]=True
    try:
        state["callback_count"]+=1; wall=time.monotonic(); state["last_tick_epoch"]=time.time()
        if state["phase"]=="exit":
            if time.monotonic()>=state["deadline"]:
                unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic()>state["deadline"]:
            finish("Wall-clock timeout during "+state["phase"]); return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:
            state["setup_polls"]+=1
            if wall-state["last_heartbeat"]>=2.0: save(); state["last_heartbeat"]=wall
            return
        if state["phase"]=="startup": state["phase"]="setup"
        if state["phase"]=="setup":
            player=unreal.GameplayStatics.get_player_pawn(game,0)
            if not player:
                state["setup_polls"]+=1
                if wall-state["last_heartbeat"]>=2.0: save(); state["last_heartbeat"]=wall
                return
            state.update(game=game,player=player,case_index=0)
            report["player_class"]=player.get_class().get_name()
            controller=player.get_controller()
            report["controller_class"]=controller.get_class().get_name() if controller else None
            report["controller_move_input_ignored_before"]=controller.is_move_input_ignored() if controller else None
            if controller: controller.set_ignore_move_input(False)
            move=player.get_movement_component(); report["movement_mode_before"]=str(move.get_editor_property("movement_mode"))
            report["max_walk_speed_cm_s"]=move.get_editor_property("max_walk_speed")
            report["game_paused_before"]=bool(unreal.GameplayStatics.is_game_paused(game))
            report["unpause_result"]=bool(unreal.GameplayStatics.set_game_paused(game,False))
            state["world_paused"]=bool(unreal.GameplayStatics.is_game_paused(game))
            unreal.SystemLibrary.execute_console_command(game,"t.IdleWhenNotForeground 0")
            report["background_tick_cvar_set"]="t.IdleWhenNotForeground 0"
            unreal.GameplayStatics.set_global_time_dilation(game,time_dilation)
            start_leg(False,True); return
        if unreal.GameplayStatics.is_game_paused(game):
            report["unpause_result"]=bool(unreal.GameplayStatics.set_game_paused(game,False))
        state["world_paused"]=bool(unreal.GameplayStatics.is_game_paused(game))
        route=state["route"]; player=state["player"]; pos=player.get_actor_location(); now=unreal.GameplayStatics.get_time_seconds(game)
        state["last_game_time_seconds"]=now; state["last_player_position_cm"]=pos.to_tuple(); state["last_player_velocity_cm_s"]=player.get_velocity().to_tuple()
        if wall-state["last_heartbeat"]>=2.0: save(); state["last_heartbeat"]=wall
        prior_pos=state.get("last_motion_position"); velocity=player.get_velocity().to_tuple(); velocity_magnitude=math.sqrt(sum(component*component for component in velocity))
        if prior_pos and (dist(pos,prior_pos)>15.0 or velocity_magnitude>20.0):
            state["last_wall_progress"]=wall; state["last_motion_position"]=pos
        elif state.get("last_wall_progress") is not None and wall-state["last_wall_progress"]>15.0:
            report["stuck_location_cm"]=pos.to_tuple(); finish("No player movement for 15 wall-clock seconds; see runner heartbeat for PIE pause/tick state"); return
        while state["index"]<len(route)-1 and dist(pos,route[state["index"]])<190: state["index"]+=1
        if state["index"]>state["last_index"]: state.update(last_index=state["index"],last_progress=now)
        if now-state["last_progress"]>20: report["stuck_location_cm"]=pos.to_tuple(); finish("No waypoint progress for 20 game seconds"); return
        if pos.z<route[state["index"]].z-180: report["fall_location_cm"]=pos.to_tuple(); finish("Player fell below the authored route surface"); return
        current=report["tests"][-1]
        if now-current.get("last_sample_seconds",-10)>=5:
            current["samples"].append({"index":state["index"],"position_cm":pos.to_tuple(),"seconds":round(now-state["start"],2),"velocity_cm_s":player.get_velocity().to_tuple()})
            current["last_sample_seconds"]=now; save()
        if state["index"]==len(route)-1 and dist(pos,route[-1])<170:
            current['end_height_error_cm']=pos.z-(route[-1].z+116.)
            if abs(current['end_height_error_cm'])>80.:
                finish('Reached endpoint XY on the wrong floor height'); return
            current.update(success=True,seconds=round(now-state["start"],2),finish_cm=pos.to_tuple())
            if not state["reverse"]: start_leg(True,False)
            elif state["case_index"]<len(CASES)-1: state["case_index"]+=1; start_leg(False,True)
            else: report["success"]=not report["errors"] and all(item["success"] for item in report["tests"]); finish()
            return
        ti=state["index"]
        while ti<len(route)-1 and dist(pos,route[ti])<180: ti+=1
        d=route[ti]-pos; length=max(1.0,math.hypot(d.x,d.y))
        player.add_movement_input(unreal.Vector(d.x/length,d.y/length,0),1.0,True)
    except Exception:
        finish(traceback.format_exc())
    finally: state["busy"]=False

world=unreal.EditorLevelLibrary.get_editor_world()
if not world or world.get_name()!="LV_Carnival": world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
if not world: raise RuntimeError("Could not load connected Carnival map")
for actor in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    if actor.get_class().get_name()=="MetaHumanMassSpawner":
        report["excluded_editor_only_spawners"].append(actor.get_actor_label())
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
report["editor_world_name"]=world.get_name(); report["startup_phase"]="map_ready"; save()
state["phase"]="startup"; state["deadline"]=time.monotonic()+300
handle=unreal.register_slate_post_tick_callback(tick)
report["startup_phase"]="callback_registered"; save()
le.editor_request_begin_play()
report["play_requested"]=True; save()
