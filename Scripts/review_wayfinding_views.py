"""Saved-level sign readability views from supported eye-height points on walked routes.

This is an editor rendering check, not runtime camera or controller acceptance.
"""
import json,math,os,sys,time,traceback
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from wayfinding_layout import ROOT,TAG
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
REV=os.environ.get('CARNIVAL_WAYFINDING_REVISION','20261029_v5')
AUTHOR=json.loads((ROOT/('Saved/WorldExpansion/Wayfinding_'+REV+'/index.json')).read_text());assert AUTHOR['success']
VIEW=os.environ.get('CARNIVAL_WAYFINDING_VIEW',REV)
OUT=ROOT/('Saved/WorldExpansion/WayfindingViews_'+VIEW);OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);EDITOR=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
R={'success':False,'errors':[],'shots':[],'rhi_requested':os.environ.get('CARNIVAL_RENDER_RHI','project default'),
   'limits':'Saved-world editor game view, 90 degree FOV, 165 cm eye height on supported sampled walking routes; no runtime-camera/controller acceptance.'}
S={'phase':'setup','i':0,'busy':False,'until':time.monotonic()+3,'deadline':time.monotonic()+1200}
samples=[]
for source in ('WorldExpansion/Walk_Route_Playtest_CappedEdges_20261029.json','IndustrialHospital/Route_Playtest_After_PropResite_20261001.json'):
 for test in json.loads((ROOT/'Saved'/source).read_text())['tests']:
  if source.startswith('Industrial') and not test['name'].startswith('walk'):continue
  points=[p.get('position_cm',p.get('position')) for p in test['samples']]
  for a,b in zip(points,points[1:]):
   n=max(1,math.ceil(math.dist(a[:2],b[:2])/100))
   for j in range(n+1):samples.append(tuple(a[k]+(b[k]-a[k])*j/n for k in range(3)))
SHOTS=[(site,face) for site in AUTHOR['signs'] for face in site['faces']]
def save():
 p=OUT/'index.tmp';p.write_text(json.dumps(R,indent=2));p.replace(OUT/'index.json')
def hit(h):
 d=h.to_tuple() if h else None
 return d if d and d[0] else None
def finish(error=None):
 if error:R['errors'].append(error)
 R['success']=not R['errors'] and len(R['shots'])==len(SHOTS) and all(s.get('image') for s in R['shots'])
 try:save()
 finally:
  unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if now<S['until']:return
  if now>S['deadline']:raise RuntimeError('Saved-view review timeout')
  if S['phase']=='setup':
   world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
   S['world']=world;actors=EA.get_all_level_actors()
   R['preview_lighting']={}
   for level in unreal.EditorLevelUtils.get_levels(world):
    name=level.get_path_name().split(':PersistentLevel')[0].split('.')[0].rsplit('/',1)[-1]
    if name in ('Lv_LightingDay','Lv_LightingNight','Lv_LightingNightSnow'):
     visible=name=='Lv_LightingNightSnow';unreal.EditorLevelUtils.set_level_visibility(level,visible,True)
     R['preview_lighting'][name]=visible
   tagged=[a for a in actors if TAG in [str(t) for t in a.tags]]
   R['saved_actor_count']=len(tagged);assert len(tagged)==AUTHOR['actors']
   R['saved_texts']=[str(a.get_component_by_class(unreal.TextRenderComponent).get_editor_property('text')) for a in tagged if a.get_component_by_class(unreal.TextRenderComponent)]
   assert len(R['saved_texts'])==sum(len(f['rows']) for s in AUTHOR['signs'] for f in s['faces'])
   S['ignore']=[a for a in actors if isinstance(a,unreal.PhysicsVolume) or a.get_actor_label().startswith('SM_Landscape_Far_01a')]
   R['hidden_editor_backdrops']=[]
   for actor in actors:
    if actor.get_actor_label().startswith('SM_Landscape_Far_01a'):
     actor.set_is_temporarily_hidden_in_editor(True);R['hidden_editor_backdrops'].append(actor.get_path_name())
   S['visual_ignore']=S['ignore']+tagged
   for actor in actors:
    if actor.get_class().get_name()=='MetaHumanMassSpawner':EA.destroy_actor(actor)
   S['camera']=EA.spawn_actor_from_class(unreal.CameraActor,V())
   S['camera'].camera_component.set_editor_property('field_of_view',90)
   # A diagnostic exposure isolates lettering from the still-open world-lighting pass.
   volume=EA.spawn_actor_from_class(unreal.PostProcessVolume,V())
   volume.set_editor_property('unbound',True);volume.set_editor_property('priority',10000.)
   settings=volume.get_editor_property('settings')
   for key,value in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
     'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
     'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':0.}.items():settings.set_editor_property(key,value)
   volume.set_editor_property('settings',settings)
   for command in ('r.Fog 0','r.VolumetricFog 0','r.EyeAdaptationQuality 2'):
    unreal.SystemLibrary.execute_console_command(world,command)
   R['preview_controls']={'manual_exposure_bias':0,'physical_camera_exposure':False,'fog':False,'bloom':False,
     'scope':'Diagnostic lettering/layout only; no gameplay lighting acceptance. Unsaved preview settings.'}
   LE.editor_set_game_view(True);LE.set_level_viewport_fov(90,unreal.Name('None'))
   S.update(phase='place',until=now+3);save();return
  if S['phase']=='place':
   if S['i']>=len(SHOTS):finish();return
   site,face=SHOTS[S['i']];base=V(*site['base']);normal=V(*face['normal']);target=base+V(0,0,355)
   candidates=[]
   for p in samples:
    delta=V(p[0]-base.x,p[1]-base.y,0);distance=delta.length()
    if distance<250 or distance>2200 or abs(p[2]-98.15-base.z)>250:continue
    alignment=delta.normal().dot(normal)
    if alignment>=.55:candidates.append((abs(distance-1250)+300*(1-alignment),p))
   chosen=None;rejected=[]
   for score,p in sorted(candidates,key=lambda x:x[0]):
    floor=hit(unreal.SystemLibrary.line_trace_single(S['world'],V(p[0],p[1],p[2]+150),V(p[0],p[1],p[2]-400),unreal.TraceTypeQuery.ECC_VISIBILITY,False,S['ignore'],unreal.DrawDebugTrace.NONE,True))
    if not floor or floor[7].z<.7:continue
    eye=floor[5]+V(0,0,165)
    occluded=hit(unreal.SystemLibrary.line_trace_single(S['world'],eye,target,unreal.TraceTypeQuery.ECC_VISIBILITY,False,S['visual_ignore'],unreal.DrawDebugTrace.NONE,True))
    if occluded:
     if len(rejected)<5:rejected.append(occluded[9].get_actor_label() if occluded[9] else 'unknown')
     continue
    chosen=eye;break
   if chosen is None:
    R['errors'].append('No visible supported view: '+site['id']+' '+face['name'])
    R['shots'].append({'id':site['id'],'face':face['name'],'image':None,'rejected':rejected});save()
    S.update(i=S['i']+1,until=now+.1);return
   rotation=unreal.MathLibrary.find_look_at_rotation(chosen,target)
   S['camera'].set_actor_location(chosen,False,True);S['camera'].set_actor_rotation(rotation,False)
   EDITOR.set_level_viewport_camera_info(chosen,rotation);LE.editor_set_game_view(True)
   path=OUT/(site['id']+'_'+face['name']+'.png')
   S.update(phase='capture',until=now+4,path=path,rec={'id':site['id'],'face':face['name'],'camera':chosen.to_tuple(),
       'rotation':rotation.to_tuple(),'text':[r['text'] for r in face['rows']]});return
  if S['phase']=='capture':
   unreal.SystemLibrary.execute_console_command(S['world'],'HighResShot 1280x720 filename="'+str(S['path']).replace('\\','/')+'"')
   S.update(phase='shot',until=now+.5,shot_deadline=now+60);return
  if S['phase']=='shot':
   if S['path'].exists() and S['path'].stat().st_size>10000:
    S['rec']['image']=str(S['path']);R['shots'].append(S['rec']);save();S.update(phase='place',i=S['i']+1,until=now+.5)
   elif now>S['shot_deadline']:raise RuntimeError('Screenshot missing: '+str(S['path']))
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();handle=unreal.register_slate_post_tick_callback(tick)
