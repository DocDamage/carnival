"""Add double-sided surface direction signs and paint guides through the real prison gap.

Save only the connectors level. Back up before/after on D:; never change the root map.
The survey tests post space against world-static/dynamic objects, including fence caps.
"""
import hashlib,json,math,os,shutil,sys,traceback
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from wayfinding_layout import ROOT,LEVEL,TAG,SITES
REV=os.environ.get('CARNIVAL_WAYFINDING_REVISION','20261029_v5')
OUT=ROOT/('Saved/WorldExpansion/Wayfinding_'+REV);OUT.mkdir(parents=True,exist_ok=False)
BACKUP=Path('D:/CarnivalBackups')/('wayfinding_'+REV);BACKUP.mkdir(parents=True,exist_ok=False)
LEVELFILE=ROOT/('Content/Carnival/World/Levels/'+LEVEL+'.umap')
MAINFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
SURVEY=ROOT/('Saved/WorldExpansion/'+os.environ.get('CARNIVAL_WAYFINDING_SURVEY','WayfindingSurvey_20261029_v4')+'.json')
V=unreal.Vector;UP=V(0,0,1);R={'success':False,'errors':[],'signs':[],'paint':[],'actors':0}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hit(h):
 d=h.to_tuple() if h else None
 return d if d and d[0] else None
def material(name,color):
 package='/Game/Carnival/World/Materials/Wayfinding';path=package+'/'+name
 existing=unreal.load_asset(path)
 if existing:return existing
 m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,package,unreal.Material,unreal.MaterialFactoryNew());assert m
 m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 node=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant3Vector)
 node.set_editor_property('constant',unreal.LinearColor(*color,1))
 assert unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 unreal.MaterialEditingLibrary.recompile_material(m);assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
 return m
try:
 plan=json.loads(SURVEY.read_text());assert plan['success'],plan['errors']
 R.update(root_before=sha(MAINFILE),level_before=sha(LEVELFILE),survey=str(SURVEY),layout_sha256=sha(ROOT/'Scripts/wayfinding_layout.py'))
 for target in (OUT/(LEVEL+'.before.umap'),BACKUP/(LEVEL+'.before.umap')):
  shutil.copy2(LEVELFILE,target);assert sha(target)==R['level_before']
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 ea=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 for actor in list(ea.get_all_level_actors()):
  if TAG in [str(t) for t in actor.tags]:
   assert '/'+LEVEL+'.' in actor.get_path_name();ea.destroy_actor(actor)
 assert le.set_current_level_by_name(LEVEL)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube');font=unreal.load_asset('/Engine/EngineFonts/RobotoDistanceField')
 textmat=unreal.load_asset('/Engine/EngineMaterials/UnlitText');assert cube and font and textmat
 dark=material('M_RouteSign_Dark',(0.012,0.030,0.025))
 paint=material('M_RouteSign_Paint',(0.56,0.49,0.34))
 metal=material('M_RouteSign_Post',(0.05,0.06,0.055))
 def mark(a,label):
  assert '/'+LEVEL+'.' in a.get_path_name();a.set_actor_label(label);a.set_folder_path('Wayfinding');a.tags=[unreal.Name(TAG)]
  R['actors']+=1;return a
 def box(label,pos,dimensions,rot,mat,collision='NoCollision'):
  a=mark(ea.spawn_actor_from_class(unreal.StaticMeshActor,pos,rot),label)
  c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,mat);c.set_collision_profile_name(collision)
  c.set_editor_property('cast_shadow',False);a.set_actor_scale3d(V(*(d/100 for d in dimensions)));return a
 def bar(label,a,b,normal,width=5):
  direction=b-a
  return box(label,(a+b)*.5,(direction.length(),width,.8),unreal.MathLibrary.make_rot_from_xz(direction.normal(),normal),paint)
 by={r['id']:r for r in plan['sites']}
 for key,center,yaw,offset,front,back in SITES:
  site=by[key];base=V(*site['base']);rotation=unreal.Rotator(yaw=float(yaw));prefix='Wayfinding_'+key
  box(prefix+'_Post',base+V(0,0,220),(14,14,440),rotation,metal,'BlockAll')
  box(prefix+'_Frame',base+V(0,0,355),(12,336,150),rotation,paint)
  box(prefix+'_Panel',base+V(0,0,355),(16,330,144),rotation,dark)
  rec={'id':key,'base':site['base'],'road_center':center,'yaw':yaw,'support':site['support'],
       'route_clearance_cm':site['route_clearance_cm'],'faces':[]}
  for face,angle,rows in (('front',yaw+180,front),('back',yaw,back)):
   radians=math.radians(angle);normal=V(math.cos(radians),math.sin(radians),0);right=V(-math.sin(radians),math.cos(radians),0)
   face_rec={'name':face,'normal':normal.to_tuple(),'rows':[]}
   for i,(label,direction) in enumerate(rows):
    z=355+(len(rows)-1)*22-i*44;stem=prefix+'_'+face+'_'+str(i)
    text=mark(ea.spawn_actor_from_class(unreal.TextRenderActor,base+UP*z+normal*9-right*38,unreal.Rotator(yaw=float(angle))),stem+'_Text')
    comp=text.get_component_by_class(unreal.TextRenderComponent);comp.set_font(font);comp.set_text_material(textmat)
    comp.set_text(label);comp.set_world_size(30);comp.set_text_render_color(unreal.Color(225,216,184,255))
    comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    comp.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    comp.set_collision_profile_name('NoCollision')
    theta=math.radians(direction);d=right*math.sin(theta)+UP*math.cos(theta);cross=normal.cross(d).normal()
    c=base+UP*z+normal*10+right*120;tip=c+d*20
    bar(stem+'_Shaft',c-d*17,tip,normal)
    bar(stem+'_ArrowA',tip,c+d*5+cross*12,normal)
    bar(stem+'_ArrowB',tip,c+d*5-cross*12,normal)
    face_rec['rows'].append({'text':label,'direction_degrees':direction})
   rec['faces'].append(face_rec)
  R['signs'].append(rec)
 # Follow the same tested geometry through the 2.9 m opening, without adding collision.
 source=(ROOT/'Scripts/playtest_world_expansion_walk_routes.py').read_text();ns={}
 exec(compile(source[:source.index('lab=resample(')],'tested_spine_geometry','exec'),ns)
 ignored=[a for a in ea.get_all_level_actors() if isinstance(a,unreal.PhysicsVolume) or a.get_actor_label().startswith('SM_Landscape_Far_01a') or TAG in [str(t) for t in a.tags]]
 for a,b in zip(ns['outer'],ns['outer'][1:]):
  if min(math.dist(a[:2],(-30158,-24842)),math.dist(b[:2],(-30158,-24842)))>2200:continue
  av,bv=V(*a),V(*b);n=max(1,math.ceil((bv-av).length()/100));step=(bv-av)/n
  heading=V(step.x,step.y,0).normal();side=V(-heading.y,heading.x,0)
  for j in range(n):
   center=av+step*(j+.5)
   for sign in (-1,1):
    p=center+side*(85*sign);ends=[]
    for q in (p-heading*52,p+heading*52):
     h=hit(unreal.SystemLibrary.line_trace_single(world,q+V(0,0,150),q-V(0,0,300),unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignored,unreal.DrawDebugTrace.NONE,True))
     if h and h[7].z>.7:ends.append(h[5])
    if len(ends)!=2 or abs(ends[0].z-ends[1].z)>5:continue
    delta=ends[1]-ends[0]
    box('Wayfinding_PrisonGateGuide',(ends[0]+ends[1])*.5+UP*2.5,(delta.length(),8,.8),unreal.MathLibrary.make_rot_from_xz(delta.normal(),UP),paint)
    R['paint'].append([(ends[0]+ends[1]).x/2,(ends[0]+ends[1]).y/2,(ends[0]+ends[1]).z/2+2.5])
 assert len(R['signs'])==len(SITES) and len(R['paint'])>=20
 package=next(a for a in ea.get_all_level_actors() if TAG in [str(t) for t in a.tags]).get_outermost()
 assert unreal.EditorLoadingAndSavingUtils.save_packages([package],False)
 R.update(root_after=sha(MAINFILE),level_after=sha(LEVELFILE));assert R['root_after']==R['root_before']
 shutil.copy2(LEVELFILE,BACKUP/LEVELFILE.name);assert sha(BACKUP/LEVELFILE.name)==R['level_after']
 R.update(external_backup=str(BACKUP),success=True)
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=2))
