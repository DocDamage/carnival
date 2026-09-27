"""Build the connected coastal sublevel and attach it and the mansion to Carnival.

Run in a rendered editor so landscape edit layers finish before saving.
"""
import sys,json,math,time,random,traceback,hashlib
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
eal=unreal.EditorAssetLibrary;eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools=unreal.AssetToolsHelpers.get_asset_tools()
report={'phase':'importing','removed':[],'meshes':[],'terrain':{}}
def record():(OUT/'Connection_Build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
record()
materials={'Gravel':unreal.load_asset('/Game/RailBridge/Materials/MI_Gravel'),
           'Shoulder':unreal.load_asset('/Game/Mansion/Materials/Buildings_Instances/MI_RoadGround'),
           'Timber':unreal.load_asset('/Game/RailBridge/Materials/MI_Wood')}
manifest=json.loads((OUT/'Route_Meshes.json').read_text())
for item in manifest:
    if item['name']=='SM_RouteImportProbe':continue
    task=unreal.AssetImportTask();task.filename=str(OUT/'Source/FBX'/(item['name']+'.fbx'))
    task.destination_path=BASE+'/Meshes';task.destination_name=item['name'];task.automated=True;task.replace_existing=True;task.save=True
    options=unreal.FbxImportUI();options.automated_import_should_detect_type=False;options.import_as_skeletal=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;options.import_materials=False;options.import_textures=False;options.import_animations=False
    data=options.static_mesh_import_data
    for key,val in {'convert_scene':True,'convert_scene_unit':True,'combine_meshes':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False}.items():data.set_editor_property(key,val)
    task.options=options;asset_tools.import_asset_tasks([task])
    mesh=unreal.load_asset(BASE+'/Meshes/'+item['name']);assert mesh
    bound=mesh.get_bounding_box()
    assert max(abs(bound.min.to_tuple()[i]-item['bounds_min'][i]) for i in range(3))<1.0,(item['name'],str(bound))
    slots=list(mesh.get_editor_property('static_materials'))
    for i,slot in enumerate(slots):
        name=str(slot.material_slot_name)
        slot.material_interface=materials.get(name,materials[item['slots'][min(i,len(item['slots'])-1)]])
    mesh.set_editor_property('static_materials',slots)
    body=mesh.get_editor_property('body_setup');assert body
    body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    body.set_editor_property('double_sided_geometry',True)
    eal.save_loaded_asset(mesh)
    report['meshes'].append(mesh.get_path_name())
record()

source_path=ROOT/'Content/RailBridge/Maps/testmap.umap'
report['source_coast_sha256']=hashlib.sha256(source_path.read_bytes()).hexdigest()
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/RailBridge/Maps/testmap')
assert unreal.EditorLoadingAndSavingUtils.save_map(world,COAST)
world=unreal.EditorLoadingAndSavingUtils.load_map(COAST)
assert world.get_path_name().startswith(COAST+'.')
unreal.CarnivalWorldEditorLibrary.clear_connected_level_demo_events(world)
remove_types={'PlayerStart','FirstPersonCharacter_C','BP_Train_C','BlockingVolume','CineCameraActor','CameraActor','SkyLight','DirectionalLight','SkyAtmosphere','VolumetricCloud','ExponentialHeightFog','PostProcessVolume'}
for a in list(eas.get_all_level_actors()):
    if a.get_class().get_name() in remove_types or a.get_actor_label() in {'Floor','SM_SkySphere2'}:
        report['removed'].append({'label':a.get_actor_label(),'class':a.get_class().get_name()});eas.destroy_actor(a)
land=next(a for a in eas.get_all_level_actors() if isinstance(a,unreal.Landscape))
world.get_world_settings().set_editor_property('default_game_mode',None)
heights=json.loads((OUT/'Mansion_Ground_Heights.json').read_text())
minimum=heights['minimum']
origin=mansion_point((minimum,minimum,0))
tf=unreal.Transform(location=unreal.Vector(*origin),rotation=unreal.Rotator(pitch=0,yaw=MANSION_LOCAL_YAW,roll=0),scale=unreal.Vector(1,1,1))
assert unreal.CarnivalWorldEditorLibrary.stamp_landscape_height_grid(land,tf,heights['size'],heights['size'],heights['spacing'],heights['heights'],2000)
report['terrain']['mansion_ground_stamp']=True
# The coastal surface remains below the existing Carnival floor, then blends out.
pad=unreal.Transform(location=unreal.Vector(-77000,-17000,0))
assert unreal.CarnivalWorldEditorLibrary.stamp_landscape_height_grid(land,pad,3,3,18000,[320.0]*9,8000)
report['terrain']['carnival_ground_join']=True
for section in SECTIONS:
    if section['surface']=='gravel':
        points=[unreal.Vector(p[0],p[1],p[2]-16) for p in section['points']]
        assert unreal.CarnivalWorldEditorLibrary.grade_landscape_route(land,points,400,1500)
report['terrain']['land_approaches_graded']=True
for path in report['meshes']:
    mesh=unreal.load_asset(path)
    actor=eas.spawn_actor_from_object(mesh,unreal.Vector(0,0,0),unreal.Rotator(pitch=0,yaw=0,roll=0))
    actor.set_actor_label(mesh.get_name().replace('SM_','Route_'));actor.set_folder_path('Connected Route/Surface')
    actor.tags=['Carnival.MansionRoute.Surface']

def sign(p,heading,label,name):
    angle=math.radians(heading);n=(-math.sin(angle),math.cos(angle))
    x,y,z=p[0]+n[0]*850,p[1]+n[1]*850,p[2]
    cube=unreal.load_asset('/Engine/BasicShapes/Cube')
    for suffix,height,scale in [('Post',100,(.16,.16,2.0)),('Board',205,(.13,2.65,1.25))]:
        a=eas.spawn_actor_from_object(cube,unreal.Vector(x,y,z+height),unreal.Rotator(pitch=0,yaw=heading,roll=0))
        a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_material(0,materials['Timber'])
        a.set_actor_label(name+'_'+suffix);a.set_folder_path('Connected Route/Wayfinding')
    text=eas.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(x-math.cos(angle)*8,y-math.sin(angle)*8,z+238),unreal.Rotator(pitch=0,yaw=heading+180,roll=0))
    comp=text.get_component_by_class(unreal.TextRenderComponent)
    comp.set_text(label);comp.set_world_size(27);comp.set_text_render_color(unreal.Color(229,220,182,255))
    comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    text.set_actor_label(name+'_Lettering');text.set_folder_path('Connected Route/Wayfinding')
sign(SECTIONS[0]['points'][7],0,'HAUNTED MANSION\nVIA WETLANDS\n1 km','Sign_Carnival_Mansion')
sign((-13000,0,430),0,'OLD RAIL CROSSING\nHAUNTED MANSION\n650 m','Sign_West_Bridge')
sign((30500,-4500,480),-12,'HAUNTED MANSION\nKEEP TO THE TRAIL\n200 m','Sign_East_Mansion')
sign((44800,-7100,838),180,'CARNIVAL\nVIA RAIL CROSSING\n1 km','Sign_Mansion_Carnival')
report['phase']='waiting_for_terrain';record()
state={'deadline':time.monotonic()+20,'phase':'finish_coast','busy':False}

def complete():
    unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
def tick(delta):
    if state['busy'] or time.monotonic()<state['deadline']:return
    state['busy']=True
    try:
        if state['phase']=='finish_coast':
            # Instancing preserves foliage density without thousands of new actors.
            rng=random.Random(84312);points=[]
            for section in SECTIONS:
                if section['surface']!='gravel':continue
                path=section['points']
                for i in range(1,len(path)-1,3):
                    p=path[i];q=path[i+1];yaw=math.atan2(q[1]-p[1],q[0]-p[0]);n=(-math.sin(yaw),math.cos(yaw))
                    for side in [-1,1]:
                        for j in range(3):
                            offset=side*rng.uniform(570,1900)
                            points.append(unreal.Vector(p[0]+n[0]*offset+rng.uniform(-150,150),p[1]+n[1]*offset+rng.uniform(-150,150),0))
            zs=unreal.CarnivalWorldEditorLibrary.sample_landscape_heights(land,points)
            transforms=[]
            for p,z in zip(points,zs):
                p.z=z-2;s=rng.uniform(.85,1.55)
                transforms.append(unreal.Transform(location=p,rotation=unreal.Rotator(pitch=0,yaw=rng.uniform(0,360),roll=0),scale=unreal.Vector(s,s,s)))
            mesh=unreal.load_asset('/Game/RailBridge/Meshes/Foliage/SM_BigGrassPatch_01a')
            grass=unreal.CarnivalWorldEditorLibrary.create_mesh_instances(world,mesh,transforms,'Wetland_Trail_Reeds',False)
            grass.set_folder_path('Connected Route/Vegetation')
            report['approach_foliage_instances']=len(transforms)
            assert unreal.EditorLoadingAndSavingUtils.save_map(world,COAST)
            assert hashlib.sha256(source_path.read_bytes()).hexdigest()==report['source_coast_sha256'],'Source coastal map changed'
            eal.save_directory(BASE,only_if_is_dirty=True,recursive=True)
            report['phase']='connecting_carnival';record()
            main=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
            for level in list(unreal.EditorLevelUtils.get_levels(main)):
                if any(level.get_path_name().startswith(p+'.') for p in [COAST,MANSION]):
                    assert unreal.EditorLevelUtils.remove_level_from_world(level)
            for path,loc,yaw in [(COAST,COAST_ORIGIN,COAST_YAW),(MANSION,world_point(MANSION_LOCAL),COAST_YAW+MANSION_LOCAL_YAW)]:
                transform=unreal.Transform(location=unreal.Vector(*loc),rotation=unreal.Rotator(pitch=0,yaw=yaw,roll=0),scale=unreal.Vector(1,1,1))
                streaming=unreal.EditorLevelUtils.add_level_to_world_with_transform(main,path,unreal.LevelStreamingAlwaysLoaded,transform)
                assert streaming,path
                streaming.set_editor_property('should_be_visible',True)
            assert unreal.EditorLoadingAndSavingUtils.save_map(main,CARNIVAL)
            report['levels']=[level.get_path_name() for level in unreal.EditorLevelUtils.get_levels(main)]
            report['phase']='complete';report['main_map']=main.get_path_name();record()
            unreal.log('MANSION_COAST_CONNECTION_SAVED');state.update(phase='exit',deadline=time.monotonic()+3)
        elif state['phase']=='exit':complete()
    except Exception:
        report['error']=traceback.format_exc();record();complete()
    finally:state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
