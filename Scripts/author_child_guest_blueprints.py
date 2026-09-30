"""Create separately fitted child guest Blueprints with supplied bodies and idle.

Does not delete/reparent existing guest assets or place static substitutes into
the game world. Roaming/social/seat animation logic and world placement follow.
"""
import datetime,json,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
census=json.loads((OUT/'Child_Animation_Source_Census.json').read_text());assert census['success']
CANDIDATE=os.environ.get('CARNIVAL_CHILD_CONSISTENT_BIND')=='1'
if CANDIDATE:
    candidate=json.loads((OUT/'BlackBoy_ConsistentBind_Import.json').read_text());assert candidate['success']
    census['children']=[dict(next(c for c in census['children'] if c['identity']=='BlackBoy'),mesh=candidate['mesh'],mesh_bounds_cm=candidate['mesh_bounds_cm'])]
elif (OUT/'Child_Rig_Overrides.json').exists():
    overrides=json.loads((OUT/'Child_Rig_Overrides.json').read_text())
    census['children']=[dict(c,**{k:v for k,v in overrides.get(c['identity'],{}).items() if k in ('mesh','mesh_bounds_cm','animation_folder')}) for c in census['children']]
retarget=json.loads((OUT/('BlackBoy_ConsistentBind_Retarget.json' if CANDIDATE else 'Child_Roster_Retarget.json')).read_text());assert retarget['success']
REPORT={'success':False,'children':[],'errors':[],
    'limits':'Saved concrete guest assets, idle and initial measured capsule/foot fitting. No world placement, navigation, full locomotion/social/seat behavior or rendered acceptance.'}
eal=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);data=unreal.SubobjectDataBlueprintFunctionLibrary
parent=unreal.load_class(None,'/Script/CarnivalPopulation.CarnivalGuestCharacter');assert parent
for child in census['children']:
    identity=child['identity'];folder=candidate['folder'] if CANDIDATE else '/Game/Carnival/Characters/Children/'+identity
    name='BP_ChildGuest_'+identity;path=folder+'/'+name
    try:
        blueprint=unreal.load_asset(path) if eal.does_asset_exist(path) else None
        if blueprint:
            assert eal.get_metadata_tag(blueprint,'CarnivalChildIdentity')==identity,'Unrelated asset at '+path
            file=ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset')
            backup=OUT/'Backups'/('GuestBlueprint_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/file.name
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
        else:
            factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',parent)
            blueprint=tools.create_asset(name,folder,unreal.Blueprint,factory)
            assert blueprint
            eal.set_metadata_tag(blueprint,'CarnivalChildIdentity',identity)
        mesh=unreal.load_asset(child['mesh']);assert isinstance(mesh,unreal.SkeletalMesh)
        animation=unreal.load_asset(child.get('animation_folder',folder+'/Animations')+'/Child_Manny_MM_Idle')
        assert animation.get_editor_property('skeleton')==mesh.skeleton
        half=child['mesh_bounds_cm']['height']*.5+4
        radius=max(22,min(30,half*.34))
        cdo=unreal.get_default_object(blueprint.generated_class())
        cdo.modify();cdo.set_editor_property('use_controller_rotation_yaw',False)
        components={}
        for handle in sds.k2_gather_subobject_data_for_blueprint(blueprint):
            obj=data.get_associated_object(data.get_data(handle))
            if isinstance(obj,unreal.SkeletalMeshComponent):components['mesh']=obj
            elif isinstance(obj,unreal.CapsuleComponent):components['capsule']=obj
            elif isinstance(obj,unreal.CharacterMovementComponent):components['movement']=obj
        body=components['mesh'];body.modify();body.set_skeletal_mesh_asset(mesh)
        body.set_relative_location(unreal.Vector(0,0,-half-child['mesh_bounds_cm']['minimum'][2]),False,False)
        body.set_relative_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0),False,False)
        body.override_animation_data(animation,True,True,0,1)
        body.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        capsule=components['capsule'];capsule.modify();capsule.set_capsule_size(radius,half,False)
        movement=components.get('movement') or cdo.get_movement_component();movement.modify()
        movement.set_editor_property('max_walk_speed',130 if half<65 else 180)
        movement.set_editor_property('max_step_height',min(45,child['mesh_bounds_cm']['height']*.25))
        movement.set_editor_property('orient_rotation_to_movement',True)
        unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
        assert eal.save_loaded_asset(blueprint)
        defaults=unreal.get_default_object(blueprint.generated_class())
        saved_mesh=defaults.get_editor_property('mesh');saved_capsule=defaults.get_editor_property('capsule_component')
        assert saved_mesh.get_editor_property('skeletal_mesh_asset')==mesh
        assert abs(saved_capsule.get_unscaled_capsule_half_height()-half)<.01
        REPORT['children'].append({'identity':identity,'blueprint':path,'class':blueprint.generated_class().get_path_name(),
            'mesh':mesh.get_path_name(),'idle':animation.get_path_name(),'capsule_half_height_cm':half,
            'capsule_radius_cm':radius,'mesh_relative_location_cm':saved_mesh.get_editor_property('relative_location').to_tuple(),
            'mesh_relative_rotation':str(saved_mesh.get_editor_property('relative_rotation')),
            'mesh_height_cm':child['mesh_bounds_cm']['height']})
    except Exception:
        REPORT['errors'].append(identity+': '+traceback.format_exc())
REPORT['success']=len(REPORT['children'])==(1 if CANDIDATE else 4) and not REPORT['errors']
(OUT/('BlackBoy_ConsistentBind_Guest.json' if CANDIDATE else 'Child_Guest_Blueprints.json')).write_text(json.dumps(REPORT,indent=2))
