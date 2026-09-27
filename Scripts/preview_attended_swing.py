"""Capture the real authored seat pose and attendant in the Unreal renderer."""
import json
import time
import traceback
from pathlib import Path
import unreal

OUT=Path(r'F:\Carnival\Saved\RideDevelopment')
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/Rides/Maps/L_AttendedSwingTest')
unreal.SystemLibrary.execute_console_command(world,'r.RDG.ParallelExecute 0')
unreal.SystemLibrary.execute_console_command(world,'r.ScreenPercentage 100')
ride=next(a for a in ACTORS.get_all_level_actors() if a.get_class().get_name()=='BP_Swing_Carnival_C')
staff=next(a for a in ACTORS.get_all_level_actors() if isinstance(a,unreal.CarnivalRideAttendant))
staff.mesh.set_update_animation_in_editor(True)
staff.mesh.override_animation_data(staff.idle_animation,False,False,.5,1.)
seats=list(ride.get_components_by_class(unreal.CarnivalRideSeatComponent))
seat=min(seats,key=lambda s:s.get_world_location().x)
tf=seat.get_passenger_world_transform()
player=ACTORS.spawn_actor_from_class(unreal.load_class(None,'/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C'),tf.translation,tf.rotation.rotator())
player.mesh.set_update_animation_in_editor(True)
player.mesh.override_animation_data(player.ride_seated_animation,False,False,.5,1.)
seat_pos=seat.get_world_location()
camera=ACTORS.spawn_actor_from_class(unreal.CameraActor,seat_pos+unreal.Vector(-300,-230,150))
camera.camera_component.set_editor_property('field_of_view',45.)
post=camera.camera_component.get_editor_property('post_process_settings')
for name,value in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
                   'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
                   'auto_exposure_apply_physical_camera_exposure':False}.items():post.set_editor_property(name,value)
camera.camera_component.set_editor_property('post_process_settings',post)
camera.camera_component.set_editor_property('post_process_blend_weight',1.)
shots=[('Swing_Seated_Preview',seat_pos+unreal.Vector(-300,-230,150),seat_pos+unreal.Vector(0,0,50)),
       ('Swing_Attendant_Preview',staff.get_actor_location()+unreal.Vector(-420,-310,120),staff.get_actor_location()+unreal.Vector(0,0,20))]
report={'shots':[]}
state={'index':0,'phase':'position','deadline':time.monotonic()+6,'busy':False}

def finish():
    (OUT/'Swing_Preview.json').write_text(json.dumps(report,indent=2))
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()

def tick(delta):
    if state['busy']:return
    state['busy']=True
    try:
        if time.monotonic()<state['deadline']:return
        if state['phase']=='position':
            name,pos,target=shots[state['index']]
            camera.set_actor_location(pos,False,True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos,target),True)
            state.update(phase='capture',deadline=time.monotonic()+2)
        elif state['phase']=='capture':
            name,_,_=shots[state['index']]
            state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1440,900,str(OUT/(name+'.png')),camera)
            state.update(phase='wait',deadline=time.monotonic()+.3)
        elif state['task'].is_task_done():
            report['shots'].append(str(OUT/(shots[state['index']][0]+'.png')))
            state['index']+=1
            if state['index']==len(shots):finish()
            else:state.update(phase='position')
    except Exception:
        report['error']=traceback.format_exc();finish()
    finally:state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
