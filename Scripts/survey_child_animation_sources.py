"""Read saved child mesh proportions and available source clips before retargeting."""
import json, math, traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'children':[],'animations':[],'meshes':[],'errors':[],
    'limits':'Read-only asset measurements and source census. No actor fitting or animation/render acceptance.'}
try:
    for identity in ('BlackGirl','WhiteBoy','WhiteGirl','BlackBoy'):
        source=json.loads((OUT/(identity+'_Unreal_Import.json' if identity=='BlackBoy' else identity+'_Migration.json')).read_text())
        assert source['success']
        mesh=unreal.load_asset(source['mesh']);assert isinstance(mesh,unreal.SkeletalMesh)
        bounds=mesh.get_imported_bounds()
        origin=bounds.origin;extent=bounds.box_extent
        assert all(math.isfinite(x) for x in origin.to_tuple()+extent.to_tuple())
        assert 100<extent.z*2<210, (identity,extent)
        bones=[str(n) for n in mesh.skeleton.get_reference_pose().get_bone_names()]
        REPORT['children'].append({'identity':identity,'mesh':mesh.get_path_name(),
            'skeleton':mesh.skeleton.get_path_name(),'bones':bones,'mesh_bounds_cm':{
            'minimum':(origin-extent).to_tuple(),'maximum':(origin+extent).to_tuple(),
            'height':extent.z*2},'slots':[str(s.material_slot_name) for s in mesh.materials]})
    registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
    candidates=[]
    for root in ('/Game/PlayMusicAnim','/Game/RamsterZ_FreeAnims_Volume1','/Game/Carnival/Character',
                 '/Game/Carnival/Vehicles/Motorcycle'):
        for data in registry.get_assets_by_path(root,True):
            name=str(data.asset_name);kind=str(data.asset_class_path.asset_name)
            if kind=='AnimSequence' and any(x in name.lower() for x in ('walk','run','idle','sit','seat','riding','talkgesture')):
                clip=data.get_asset();assert isinstance(clip,unreal.AnimSequence)
                candidates.append(clip)
            elif kind=='AnimMontage' and any(x in name.lower() for x in ('riding','seat','sit')):
                for dependency in registry.get_dependencies(str(data.package_name),unreal.AssetRegistryDependencyOptions(
                        include_hard_package_references=True,include_soft_package_references=False)):
                    for referenced in registry.get_assets_by_package_name(dependency):
                        if str(referenced.asset_class_path.asset_name)=='AnimSequence':
                            candidates.append(referenced.get_asset())
    seen=set()
    for clip in candidates:
        if clip.get_path_name() in seen:continue
        seen.add(clip.get_path_name())
        REPORT['animations'].append({'path':clip.get_path_name(),'name':clip.get_name(),
            'skeleton':clip.get_editor_property('skeleton').get_path_name(),
            'seconds':clip.get_editor_property('sequence_length'),
            'root_motion':clip.get_editor_property('enable_root_motion')})
    for path in ('/Game/PlayMusicAnim/Demo/Mannequins/Meshes/SKM_Manny',
                 '/Game/RamsterZ_FreeAnims_Volume1/Demo/Mannequin/Character/Mesh/SK_Mannequin'):
        mesh=unreal.load_asset(path)
        if not isinstance(mesh,unreal.SkeletalMesh):raise RuntimeError('Source mesh missing '+path)
        REPORT['meshes'].append({'path':path,'skeleton':mesh.skeleton.get_path_name(),
            'bones':[str(n) for n in mesh.skeleton.get_reference_pose().get_bone_names()]})
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
(OUT/'Child_Animation_Source_Census.json').write_text(json.dumps(REPORT,indent=2))
