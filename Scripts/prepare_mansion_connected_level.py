"""Preserve the authored mansion interior and nearby grounds in a reusable sublevel."""
import sys,json,hashlib
from pathlib import Path
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import OUT,BASE,MANSION
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal=unreal.EditorAssetLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools()
src=Path(r'F:\Carnival\Content\Mansion\Levels\LV_Haunted_Mansion.umap')
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed':[],'foliage':[]}
# Check the FBX axes once, before importing or placing the complete road.
task=unreal.AssetImportTask();task.filename=str(OUT/'Source/FBX/SM_RouteImportProbe.fbx');task.destination_path=BASE+'/Meshes';task.destination_name='SM_RouteImportProbe'
task.automated=True;task.replace_existing=True;task.save=True
opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
opt.static_mesh_import_data.set_editor_property('convert_scene',True);opt.static_mesh_import_data.set_editor_property('convert_scene_unit',True)
task.options=opt;tools.import_asset_tasks([task])
probe=unreal.load_asset(BASE+'/Meshes/SM_RouteImportProbe');b=probe.get_bounding_box()
report['probe']={'min':list(b.min.to_tuple()),'max':list(b.max.to_tuple())}
assert abs(b.min.x-900)<.1 and abs(b.min.y-1800)<.1 and abs(b.max.z-350)<.1,report['probe']
(OUT/'Mansion_Preparation.json').write_text(json.dumps(report,indent=2))

world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Mansion/Levels/LV_Haunted_Mansion')
actors=list(eas.get_all_level_actors());land=next(a for a in actors if isinstance(a,unreal.Landscape))
size=57;spacing=500.0;minimum=-14000.0
positions=[unreal.Vector(minimum+x*spacing,minimum+y*spacing,0) for y in range(size) for x in range(size)]
heights=list(unreal.CarnivalWorldEditorLibrary.sample_landscape_heights(land,positions))
assert len(heights)==size*size
(OUT/'Mansion_Ground_Heights.json').write_text(json.dumps({'size':size,'spacing':spacing,'minimum':minimum,'heights':heights}))
foliage=[]
for a in actors:
    if isinstance(a,unreal.InstancedFoliageActor):
        for component in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh=component.get_editor_property('static_mesh')
            if not mesh:continue
            transforms=[]
            for i in range(component.get_instance_count()):
                t=component.get_instance_transform(i,world_space=True)
                p=t.translation
                if abs(p.x)<11800 and abs(p.y)<11800:transforms.append(t)
            if transforms:foliage.append((mesh.get_path_name(),transforms))
assert unreal.EditorLoadingAndSavingUtils.save_map(world,MANSION)
world=unreal.EditorLoadingAndSavingUtils.load_map(MANSION)
assert world.get_path_name().startswith(MANSION+'.'),world.get_path_name()
remove_types={'Landscape','InstancedFoliageActor','PlayerStart','SkyLight','DirectionalLight','SkyAtmosphere','ExponentialHeightFog','VolumetricCloud','PostProcessVolume','LevelSequenceActor','CineCameraActor','CameraActor','WorldPartitionMiniMap','SphereReflectionCapture'}
for a in list(eas.get_all_level_actors()):
    c=a.get_class().get_name();p=a.get_actor_location();label=a.get_actor_label()
    remove=c in remove_types or 'SkySphere' in c or 'HDRI' in c or 'Landscape' in label
    if abs(p.x)>12500 or abs(p.y)>12500:remove=True
    if remove:
        report['removed'].append({'label':label,'class':c});eas.destroy_actor(a)
for mesh_path,transforms in foliage:
    mesh=unreal.load_asset(mesh_path)
    a=unreal.CarnivalWorldEditorLibrary.create_mesh_instances(world,mesh,transforms,'MansionGrounds_'+mesh.get_name(), 'tree' in mesh.get_name().lower())
    a.set_folder_path('Mansion/Grounds/Foliage')
    report['foliage'].append({'mesh':mesh.get_name(),'instances':len(transforms)})
world.get_world_settings().set_editor_property('default_game_mode',None)
assert unreal.EditorLoadingAndSavingUtils.save_map(world,MANSION)
report['actor_count']=len(eas.get_all_level_actors())
assert hashlib.sha256(src.read_bytes()).hexdigest()==report['source_sha256'],'Source mansion map changed'
(OUT/'Mansion_Preparation.json').write_text(json.dumps(report,indent=2))
unreal.log('MANSION_CONNECTED_PREPARED '+str(report['actor_count']))
