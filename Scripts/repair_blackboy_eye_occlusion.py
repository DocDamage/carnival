"""Match the supplied zero-opacity eye-occlusion layer on owned materials."""
import datetime,hashlib,json,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'changes':[],'limits':'Saved transparency binding only; requires fresh eye/face rendered review.'}
source=next((OUT/'BlackBoy/textures').rglob('Std_Eye_Occlusion_R_Opacity.jpg'))
REPORT['supplied_right_opacity_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
# Read-only offline census establishes this supplied 64px map is uniformly 0.
# The paired left layer has the same geometric role and no separately supplied
# opacity map. Preserve both layer meshes; their source intent is invisible.
mel=unreal.MaterialEditingLibrary;eal=unreal.EditorAssetLibrary
backup=OUT/'Backups'/('EyeOcclusion_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
for side in ('L','R'):
 path='/Game/Carnival/Characters/Children/BlackBoy/Materials/M_Std_Eye_Occlusion_'+side
 file=ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset')
 copy=backup/file.name;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,copy)
 material=unreal.load_asset(path);assert isinstance(material,unreal.Material)
 material.modify();material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
 material.set_editor_property('two_sided',True)
 expression=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-180,250)
 expression.set_editor_property('r',0)
 assert mel.connect_material_property(expression,'',unreal.MaterialProperty.MP_OPACITY)
 mel.recompile_material(material);assert eal.save_loaded_asset(material)
 REPORT['changes'].append({'material':path,'backup':str(copy),'opacity':0,'left_uses_paired_source_intent':side=='L'})
REPORT['success']=len(REPORT['changes'])==2
(OUT/'BlackBoy_Eye_Occlusion_Repair.json').write_text(json.dumps(REPORT,indent=2))
