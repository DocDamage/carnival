"""Save an isolated reference-alignment comparison, preserving production clips."""
import json
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
BASE='/Game/Carnival/Characters/Children/BlackBoy'
REPORT={'success':False,'limits':'Comparison clip only; no production animation replacement or visual acceptance.'}
eal=unreal.EditorAssetLibrary
destination=BASE+'/Diagnostics/RTG_Manny_ReferenceAlignment'
if not eal.does_asset_exist(destination):assert eal.duplicate_asset(BASE+'/Retarget/RTG_Manny_To_BlackBoy',destination)
asset=unreal.load_asset(destination);ctrl=unreal.IKRetargeterController.get_controller(asset)
mode=unreal.RetargetSourceOrTarget.TARGET
pose='ReferenceAlignment'
if pose not in [str(n) for n in ctrl.get_retarget_poses(mode)]:ctrl.create_retarget_pose(pose,mode)
ctrl.set_current_retarget_pose(pose,mode);ctrl.reset_retarget_pose(pose,[],mode)
assert eal.save_loaded_asset(asset)
census=json.loads((OUT/'Child_Animation_Source_Census.json').read_text())
source_clip=next(a['path'] for a in census['animations'] if a['name']=='MM_Idle')
package=source_clip.split('.')[0]
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
clip_path=BASE+'/Diagnostics/Comparison_MM_Idle_ReferenceAlignment'
if not eal.does_asset_exist(clip_path):
 inputs=unreal.IKRetargetBatchOperationInputs()
 inputs.assets_to_retarget=list(registry.get_assets_by_package_name(package))
 inputs.source_mesh=unreal.load_asset('/Game/PlayMusicAnim/Demo/Mannequins/Meshes/SKM_Manny')
 inputs.target_mesh=unreal.load_asset(BASE+'/Mesh/SK_BlackBoy')
 if not inputs.target_mesh:
  children=json.loads((OUT/'Child_Guest_Blueprints.json').read_text())['children']
  inputs.target_mesh=unreal.load_asset(next(c['mesh'] for c in children if c['identity']=='BlackBoy'))
 assert inputs.target_mesh
 inputs.ik_retarget_asset=asset;inputs.prefix='Comparison_';inputs.suffix='_ReferenceAlignment'
 inputs.target_path=BASE+'/Diagnostics';inputs.include_referenced_assets=False;inputs.overwrite_existing_files=False
 imported=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs);assert len(imported)==1
clip=unreal.load_asset(clip_path);assert isinstance(clip,unreal.AnimSequence)
assert eal.save_loaded_asset(clip)
assert (ROOT/'Content'/(clip_path.removeprefix('/Game/')+'.uasset')).is_file()
REPORT.update(success=True,clip=clip.get_path_name(),retargeter=asset.get_path_name())
(OUT/'BlackBoy_ReferenceAlignment_Comparison.json').write_text(json.dumps(REPORT,indent=2))
