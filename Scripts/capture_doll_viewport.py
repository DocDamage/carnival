"""Capture imported poses using Unreal's editor viewport renderer."""
import json,time,traceback
from pathlib import Path
import unreal
BASE='/Game/Carnival/Characters/PossessedDoll'
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
images=OUT/'Previews';images.mkdir(exist_ok=True)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_DollTest')
for actor in eas.get_all_level_actors():
    if isinstance(actor,unreal.CarnivalHauntedDoll):eas.destroy_actor(actor)
mesh=unreal.load_asset(BASE+'/SK_Doll')
camera=eas.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(380,-247,155),unreal.Rotator(pitch=-10,yaw=147,roll=0))
camera.camera_component.set_editor_property('field_of_view',40.0)
post=camera.camera_component.get_editor_property('post_process_settings')
for key,value in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
    'override_auto_exposure_bias':True,'auto_exposure_bias':-2.5,'override_auto_exposure_apply_physical_camera_exposure':True,
    'auto_exposure_apply_physical_camera_exposure':False}.items():post.set_editor_property(key,value)
camera.camera_component.set_editor_property('post_process_settings',post)
camera.camera_component.set_editor_property('post_process_blend_weight',1.0)
cases=[('Original/Doll_Idle_Possessed_Loop',.3),('Original/Doll_Walk_Twitchy_InPlace',.4),
       ('Original/Doll_Run_Twitchy_InPlace',.2),('Original/Doll_Jumpscare_Lunge',.65),
       ('RamsterZ_Volume1/Doll_RZ_Standing_Idle',.7),('RamsterZ_Volume1/Doll_RZ_Stealth_Idle',.6),
       ('RamsterZ_Volume1/Doll_RZ_TalkGesture_Dramatic01',1.5)]
stage={'index':-1,'deadline':time.monotonic()+4,'phase':'next','busy':False,'actor':None,'task':None}
report={'renderer':'Unreal Editor D3D12 viewport','poses':[]}
def finish():
    (OUT/'Unreal_Pose_Previews.json').write_text(json.dumps(report,indent=2))
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()
def advance(delta):
    if stage['busy']:return
    stage['busy']=True
    try:
        if time.monotonic()<stage['deadline']:return
        if stage['phase']=='screenshot':
            if not stage['task'].is_task_done():return
            name,seconds=cases[stage['index']]
            report['poses'].append({'animation':name,'time':seconds,'file':str(images/(name.split('/')[-1]+'.png')),
                                   'head':str(stage['actor'].skeletal_mesh_component.get_bone_transform('head'))})
            stage['phase']='next'
        if stage['phase']=='capture':
            name,seconds=cases[stage['index']]
            stage['task']=unreal.AutomationLibrary.take_high_res_screenshot(1440,810,str(images/(name.split('/')[-1]+'.png')),camera)
            stage['phase']='screenshot';stage['deadline']=time.monotonic()+.25
            return
        if stage['phase']=='next':
            stage['index']+=1
            if stage['index']==len(cases):
                unreal.log_warning('DOLL_UNREAL_PREVIEW_COMPLETE')
                finish();return
            if stage['actor']:eas.destroy_actor(stage['actor'])
            actor=eas.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0))
            actor.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
            actor.skeletal_mesh_component.set_update_animation_in_editor(True)
            name,seconds=cases[stage['index']]
            actor.skeletal_mesh_component.override_animation_data(unreal.load_asset(BASE+'/Animations/'+name),False,False,seconds,1)
            stage.update({'actor':actor,'phase':'capture','deadline':time.monotonic()+1.5})
    except Exception:
        report['error']=traceback.format_exc()
        finish()
    finally:stage['busy']=False
handle=unreal.register_slate_post_tick_callback(advance)
