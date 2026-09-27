"""Capture actual views of the saved connected map without changing its lighting."""
import sys,time,traceback,json,math
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
images=OUT/'Previews';images.mkdir(exist_ok=True)
world=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera=eas.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(0,0,10000))
camera.camera_component.set_editor_property('field_of_view',65.0)
cases=[('01_Carnival_Trail',(-50700,-500,820),(-5,COAST_YAW,0)),
       ('02_Railroad_Bridge',(-10200,-50,635),(-1,COAST_YAW,0)),
       ('03_Wetlands_Crossing',(0,-17000,15000),(-40,COAST_YAW+90,0)),
       ('04_Mansion_Approach',(44500,-7000,1090),(1,COAST_YAW,0)),
       ('05_Mansion_Exterior',(43000,-16000,6200),(-22,COAST_YAW+40,0)),
       ('06_Connected_World',(0,-65000,65000),(-45,COAST_YAW+90,0))]
state={'i':-1,'phase':'next','deadline':time.monotonic()+16,'busy':False,'task':None}
report={'images':[]}
def done():
    (OUT/'Connection_Previews.json').write_text(json.dumps(report,indent=2))
    unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
def tick(delta):
    if state['busy']:return
    state['busy']=True
    try:
        if time.monotonic()<state['deadline']:return
        if state['phase']=='shot':
            if not state['task'].is_task_done():return
            report['images'].append(str(images/(cases[state['i']][0]+'.png')));state['phase']='next'
        if state['phase']=='capture':
            state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1600,1000,str(images/(cases[state['i']][0]+'.png')),camera)
            state['phase']='shot';return
        if state['phase']=='next':
            state['i']+=1
            if state['i']>=len(cases):done();return
            name,p,r=cases[state['i']]
            camera.set_actor_location(unreal.Vector(*world_point(p)),False,True)
            camera.set_actor_rotation(unreal.Rotator(pitch=r[0],yaw=r[1],roll=r[2]),False)
            state.update(phase='capture',deadline=time.monotonic()+5)
    except Exception:
        report['error']=traceback.format_exc();done()
    finally:state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
