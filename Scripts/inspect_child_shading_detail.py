"""Read source texture pixels and material output functions without mutation."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources/ShadingDetail'
OUT.mkdir(parents=True,exist_ok=True)
census=json.loads((OUT.parent/'Child_Material_Roots.json').read_text());assert census['success']
REPORT={'success':False,'errors':[],'materials':[],'textures':[],'modified_assets':False}
mel=unreal.MaterialEditingLibrary;seen=set()
try:
 for row in census['materials']:
  if not (row['slot']=='Std_Skin_Head' or (row['identity']=='BlackGirl' and row['slot'].startswith('top')) or (row['identity']=='BlackBoy' and row['slot'].startswith('Std_Eye'))):continue
  root=unreal.load_asset(row['parent_chain'][-1]);assert root
  outputs={}
  for label,enum in [('base',unreal.MaterialProperty.MP_BASE_COLOR),('mask',unreal.MaterialProperty.MP_OPACITY_MASK),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('offset',unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)]:
   node=mel.get_material_property_input_node(root,enum)
   function=node.get_editor_property('material_function') if isinstance(node,unreal.MaterialExpressionMaterialFunctionCall) else None
   outputs[label]={'node':node.get_path_name() if node else None,'function':function.get_path_name() if function else None}
  REPORT['materials'].append({'identity':row['identity'],'slot':row['slot'],'outputs':outputs})
  textures=[x['texture'] for x in row['texture_parameters'] if x['parameter']=='Base Color Map']
  if row['identity']=='BlackBoy':
   textures=[n.get_editor_property('texture').get_path_name() for n in mel.get_material_expressions(root) if isinstance(n,unreal.MaterialExpressionTextureSample) and n.get_editor_property('texture') and 'Diffuse' in n.get_editor_property('texture').get_name()]
  for path in textures:
   if not path or path in seen:continue
   seen.add(path);texture=unreal.load_asset(path)
   file=OUT/(row['identity']+'_'+row['slot']+'_'+texture.get_name()+'.png')
   task=unreal.AssetExportTask();task.object=texture;task.filename=str(file)
   task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.TextureExporterPNG()
   assert unreal.Exporter.run_asset_export_task(task),(path,list(task.errors))
   assert file.exists()
   REPORT['textures'].append({'identity':row['identity'],'slot':row['slot'],'asset':path,'image':str(file),'srgb':texture.get_editor_property('srgb')})
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
