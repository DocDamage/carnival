"""Build the reusable Blueprint and a playable test map; inspect carnival placement."""
import json
from pathlib import Path
import unreal

BASE='/Game/Carnival/Characters/PossessedDoll'
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
eal=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
path=BASE+'/BP_PossessedDoll'
if eal.does_asset_exist(path):bp=unreal.load_asset(path)
else:
    factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.CarnivalHauntedDoll)
    bp=tools.create_asset('BP_PossessedDoll',BASE,unreal.Blueprint,factory)
cdo=unreal.get_default_object(bp.generated_class())
for prop,name in {'idle_animation':'Doll_Idle_Possessed_Loop','walk_animation':'Doll_Walk_Twitchy_InPlace',
    'run_animation':'Doll_Run_Twitchy_InPlace','notice_animation':'Doll_Head_Snap','scare_animation':'Doll_Jumpscare_Lunge',
    'reach_animation':'Doll_Reach_Grab','jump_animation':'Doll_Jump_InPlace'}.items():
    cdo.set_editor_property(prop,unreal.load_asset(BASE+'/Animations/Original/'+name))
cdo.set_editor_property('ramster_idle_animation',unreal.load_asset(BASE+'/Animations/RamsterZ_Volume1/Doll_RZ_Standing_Idle'))
cdo.set_editor_property('scare_sound',unreal.load_asset('/Game/Creepwood_Carnival_Meshingun/Environment/Asset/Audio/Source/Ride/Haunted_House_Evil_Laugh'))
mesh=unreal.load_asset(BASE+'/SK_Doll')
component=cdo.get_component_by_class(unreal.SkeletalMeshComponent)
component.set_skeletal_mesh_asset(mesh)
component.set_anim_instance_class(unreal.CarnivalDollAnimInstance)
component.set_editor_property('relative_location',unreal.Vector(0,0,-71))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
eal.save_loaded_asset(bp)

TEST_MAP=BASE+'/Maps/L_DollTest'
if not eal.does_asset_exist(TEST_MAP):
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    floor=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(250,0,-20))
    floor.set_actor_label('DollTest_Floor');floor.set_actor_scale3d(unreal.Vector(30,24,.4))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.static_mesh_component.set_material(0,unreal.load_asset('/Engine/EngineMaterials/WorldGridMaterial'))
    sun=eas.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,500),unreal.Rotator(pitch=-45,yaw=-35,roll=0))
    sun.light_component.set_editor_property('intensity',3.0)
    sun.light_component.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    sky=eas.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,450))
    sky.light_component.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('intensity',1.0)
    fill=eas.spawn_actor_from_class(unreal.PointLight,unreal.Vector(250,-200,240))
    fill.light_component.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    fill.light_component.set_editor_property('intensity',3500.0)
    fill.light_component.set_editor_property('attenuation_radius',1500.0)
    doll=eas.spawn_actor_from_class(bp.generated_class(),unreal.Vector(0,0,74))
    doll.set_actor_label('PossessedDoll_TestEncounter')
    player=eas.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(650,0,100),unreal.Rotator(pitch=0,yaw=180,roll=0))
    player.set_actor_label('PlayerStart_DollTest')
    camera=eas.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(400,-330,190),unreal.Rotator(pitch=-12,yaw=141,roll=0))
    camera.set_actor_label('DollTest_PreviewCamera')
    camera.camera_component.set_editor_property('field_of_view',48.0)
    world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,'/Game/Carnival/Blueprints/BP_CarnivalGameMode.BP_CarnivalGameMode_C'))
    assert unreal.EditorLoadingAndSavingUtils.save_map(world,TEST_MAP)

report={'blueprint':path,'test_map':TEST_MAP,'preview_api':{}}
for name in ['SceneCaptureComponent2D','SkeletalMeshComponent','RenderingLibrary','TextureRenderTarget2D','FbxExportOption','EditorLevelLibrary','AutomationLibrary','HitResult']:
    cls=getattr(unreal,name)
    report['preview_api'][name]={'doc':str(cls.__doc__),'members':{n:str(getattr(cls,n).__doc__) for n in dir(cls) if any(s in n for s in ['capture','position','animation','render_target','screenshot','viewport','bone_transform'])}}
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
report['carnival_map']=MAP
report['haunted_house']=[];report['player_starts']=[];report['ground_probes']=[]
for a in eas.get_all_level_actors():
    label=a.get_actor_label()
    if 'HauntedHouse' in label or isinstance(a,unreal.PlayerStart):
        item={'name':label,'class':a.get_class().get_name(),'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation()),'bounds':str(a.get_actor_bounds(False))}
        report['haunted_house' if 'HauntedHouse' in label else 'player_starts'].append(item)
# Height probes around the haunted house. Save only a report; the carnival
# placement is done separately after the functional encounter test passes.
for x in range(6100,9001,400):
    for y in range(2400,5601,400):
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,650),unreal.Vector(x,y,-200),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
        if hit:
            report['ground_probes'].append({'x':x,'y':y,'hit':[str(v) for v in hit.to_tuple()]})
(OUT/'Doll_Encounter_Setup.json').write_text(json.dumps(report,indent=2))
unreal.log_warning('DOLL_ENCOUNTER_SETUP_COMPLETE')
