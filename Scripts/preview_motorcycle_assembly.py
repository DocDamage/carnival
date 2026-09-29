"""Render the actual saved bike and player assets in an unsaved inspection stage."""
import json
import time
import traceback
from pathlib import Path
import unreal

config = globals().get('PREVIEW_CONFIG', {})
OUT = Path(r'F:\Carnival\Saved\DirtBike\Previews')
OUT.mkdir(parents=True, exist_ok=True)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
bike = actors.spawn_actor_from_class(unreal.load_class(None,
    '/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C'), unreal.Vector())
rider = actors.spawn_actor_from_class(unreal.load_class(None,
    '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C'), unreal.Vector(*config.get('rider_position',(-80,160,96))))
if config.get('clip'):
    rider.mesh.override_animation_data(unreal.load_asset(config['clip']),False,False,config.get('time',.75),1.)
    rider.mesh.set_update_animation_in_editor(True)
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,0,-6))
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(16,16,.1))
for pitch, yaw, strength in [(-45,-35,5.),(-30,150,2.)]:
    light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,500),
                                          unreal.Rotator(pitch=pitch,yaw=yaw,roll=0))
    light.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity', strength)
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(350,-480,230))
camera.camera_component.set_editor_property('field_of_view',45.)
settings = camera.camera_component.get_editor_property('post_process_settings')
for name,value in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
                   'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
                   'auto_exposure_apply_physical_camera_exposure':False}.items(): settings.set_editor_property(name,value)
camera.camera_component.set_editor_property('post_process_settings',settings)
camera.camera_component.set_editor_property('post_process_blend_weight',1.)
shots = config.get('shots', [('Assembly_Front', (350,-480,220),(0,0,80)),
         ('Assembly_Rear',(-350,420,180),(0,0,80)),
         ('Player_Orientation',(320,-400,180),(-40,110,85))])
report={'shots':[],'errors':[],'scope':config.get('scope','saved meshes, materials, assembly and player orientation; no runtime animation claim')}
state={'index':0,'phase':'position','deadline':time.monotonic()+12,'busy':False}

def finish():
    (OUT/config.get('report','Capture_Report.json')).write_text(json.dumps(report,indent=2))
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()

def tick(delta):
    global rider
    if state['busy']: return
    state['busy']=True
    try:
        if time.monotonic()<state['deadline']: return
        if state['phase']=='position':
            name,position,target=shots[state['index']]
            if config.get('times'):
                sample_clip=unreal.load_asset(config.get('clips',[config['clip']]*len(shots))[state['index']])
                # Editor animation data can restore the original position on
                # tick; initialize a fresh component at each sampled time.
                actors.destroy_actor(rider)
                rider = actors.spawn_actor_from_class(unreal.load_class(None,
                    '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C'),
                    unreal.Vector(*config.get('rider_positions',[config.get('rider_position',(0,0,98.195294))]*len(shots))[state['index']]))
                rider.mesh.override_animation_data(sample_clip,False,False,
                    min(config['times'][state['index']],sample_clip.get_play_length()-.0001),1.)
                rider.mesh.set_update_animation_in_editor(True)
            hidden = not config.get('show_rider',False) and state['index']!=2
            rider.set_actor_hidden_in_game(hidden)
            rider.set_is_temporarily_hidden_in_editor(hidden)
            position,target=unreal.Vector(*position),unreal.Vector(*target)
            camera.set_actor_location(position,False,True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position,target),True)
            state.update(phase='capture',deadline=time.monotonic()+3)
        elif state['phase']=='capture':
            state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1440,1000,str(OUT/(shots[state['index']][0]+'.png')),camera)
            state.update(phase='wait',deadline=time.monotonic()+.3)
        elif state['task'].is_task_done():
            if config.get('clip'):
                bone_names=['pelvis','head','upperarm_l','lowerarm_l','hand_l','thigh_l','calf_l','foot_l','ball_l',
                            'upperarm_r','lowerarm_r','hand_r','thigh_r','calf_r','foot_r','ball_r']
                report['bones']={b:list(rider.mesh.get_socket_location(b).to_tuple()) for b in bone_names}
                if config.get('times'):
                    report.setdefault('samples',[]).append({
                        'image':str(OUT/(shots[state['index']][0]+'.png')),
                        'clip':config.get('clips',[config['clip']]*len(shots))[state['index']],
                        'time_seconds':config['times'][state['index']],
                        'actor_location_cm':list(rider.get_actor_location().to_tuple()),
                        'bones_world_cm':report['bones']})
            report['shots'].append(str(OUT/(shots[state['index']][0]+'.png')))
            state['index']+=1
            if state['index']==len(shots): finish()
            else: state.update(phase='position')
    except Exception:
        report['errors'].append(traceback.format_exc());finish()
    finally:
        state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
