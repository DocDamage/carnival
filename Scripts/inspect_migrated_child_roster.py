"""Fresh main-project reload of separately migrated supplied child bodies."""
import hashlib,json,math,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');BASE=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'children':[],'errors':[],
    'full_child_roster_integrated':False,'visual_animation_clothing_seating_acceptance':False,
    'limits':'Main-project asset/rig/material-reference reload only. BlackBoy FBX import, actors/animation, physical fitting, full roster and rendered acceptance remain required.'}
skeletons=set()
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=False,
    include_hard_package_references=True,include_searchable_names=False,
    include_soft_management_references=False,include_hard_management_references=False)
for identity in ('BlackGirl','WhiteBoy','WhiteGirl'):
    try:
        transfer=json.loads((BASE/(identity+'_Migration.json')).read_text())
        if not transfer.get('success') or transfer.get('engine_exit_code')!=0:
            raise RuntimeError('No clean source transfer for '+identity)
        for asset in transfer['assets']:
            file=ROOT/'Content'/Path(asset['package'].removeprefix('/Game/')).with_suffix('.uasset')
            if hashlib.sha256(file.read_bytes()).hexdigest()!=asset['sha256']:
                raise RuntimeError('Transferred bytes changed before reload '+str(file))
        mesh=unreal.load_asset(transfer['mesh']);assert isinstance(mesh,unreal.SkeletalMesh)
        skeleton=mesh.skeleton;assert skeleton and skeleton.get_path_name()==transfer['skeleton']
        if skeleton.get_path_name() in skeletons: raise RuntimeError('Child skeletons were merged')
        skeletons.add(skeleton.get_path_name())
        pose=skeleton.get_reference_pose();bones=[str(n) for n in pose.get_bone_names()]
        required={'root','pelvis','spine_01','head','hand_l','hand_r','foot_l','foot_r'}
        if not required.issubset(bones): raise RuntimeError('Missing body bones '+str(required-set(bones)))
        reference={}
        for name in sorted(required):
            transform=pose.get_bone_pose(name,unreal.AnimPoseSpaces.WORLD)
            values=list(transform.translation.to_tuple())+list(transform.scale3d.to_tuple())
            if not all(math.isfinite(x) for x in values): raise RuntimeError('Invalid reference transform '+name)
            reference[name]={'translation_cm':transform.translation.to_tuple(),'scale':transform.scale3d.to_tuple()}
        materials=[]
        for slot in mesh.get_editor_property('materials'):
            material=slot.get_editor_property('material_interface')
            if not material: raise RuntimeError('Missing material in '+str(slot.material_slot_name))
            if not material.get_path_name().startswith(transfer['namespace']+'/'):
                raise RuntimeError('Foreign material reference '+material.get_path_name())
            materials.append({'slot':str(slot.material_slot_name),'material':material.get_path_name()})
        pending=[transfer['mesh']];visited=set()
        while pending:
            package=pending.pop()
            if package in visited or not package.startswith('/Game/'): continue
            if not package.startswith(transfer['namespace']+'/'): raise RuntimeError('Foreign hard dependency '+package)
            visited.add(package)
            assets=list(registry.get_assets_by_package_name(package))
            if len(assets)!=1 or not assets[0].get_asset(): raise RuntimeError('Cannot reload dependency '+package)
            pending.extend(str(x) for x in registry.get_dependencies(package,options))
        REPORT['children'].append({'identity':identity,'mesh':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),
            'bone_count':len(bones),'skeleton_reference_pose':reference,'material_slots':materials,
            'hard_dependencies_reloaded':len(visited),'success':True})
    except Exception:
        REPORT['errors'].append(identity+': '+traceback.format_exc())
REPORT['success']=len(REPORT['children'])==3 and not REPORT['errors']
(BASE/'MainProjectAssetReload.json').write_text(json.dumps(REPORT,indent=2))
