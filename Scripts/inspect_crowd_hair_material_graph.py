"""Read the SDK hair graph and compact atlas settings without saving assets."""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs'/os.environ.get('CARNIVAL_HAIR_GRAPH_REPORT','CrowdHairGraph_20260930');OUT.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'errors':[],'assets_saved':False,'graphs':{},'textures':[]}
ML=unreal.MaterialEditingLibrary
def path(o):return o.get_path_name() if o else None
def visit(asset):
 key=path(asset)
 if key in REPORT['graphs']:return
 row={'class':asset.get_class().get_name(),'expressions':[]};REPORT['graphs'][key]=row
 if isinstance(asset,unreal.Material):
  for n in ('blend_mode','shading_model','two_sided'):
   try:row[n]=str(asset.get_editor_property(n))
   except Exception:pass
  expressions=ML.get_material_expressions(asset)
 else:expressions=ML.get_material_function_expressions(asset)
 for expression in expressions:
  e={'path':path(expression),'class':expression.get_class().get_name()};row['expressions'].append(e)
  e['exact_inputs']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_material_expression_inputs(expression))['inputs']
  e['input_names']=[str(n) for n in ML.get_material_expression_input_names(expression)]
  inputs=ML.get_inputs_for_material_expression(asset,expression) if isinstance(asset,unreal.Material) else ML.get_inputs_for_material_function_expression(asset,expression)
  e['input_nodes']=[path(n) for n in inputs]
  e['input_output_names']=[str(ML.get_input_node_output_name_for_material_expression(expression,n)) if n else None for n in inputs]
  e['input_output_names_limit']='Legacy SDK helper returns the first matching source-node output when a node feeds multiple inputs. Use exact_inputs for per-input output indices and masks.'
  for n in ('desc','parameter_name','default_value','coordinate_index','code','texture','sampler_type','sampler_source','a','b','input','coordinates','inputs','input_name','output_name','shading_model','name','r','g','b','index','sort_priority','mask_r','mask_g','mask_b','mask_a','declaration','const_a','const_b','const_exponent','const_min','const_max','const_value','preview_value'):
   try:
    v=expression.get_editor_property(n)
    e[n]=path(v) if isinstance(v,unreal.Object) else v if isinstance(v,(str,bool,int,float)) else str(v)
   except Exception:pass
  if isinstance(expression,unreal.MaterialExpressionMaterialFunctionCall):
   child=expression.get_editor_property('material_function');e['function']=path(child)
   if child:visit(child)
try:
 material=unreal.load_asset('/MetaHumanCrowd/Materials/M_Hair_Instanced');assert material;visit(material)
 for name in ('Hair_M_UpdoDutchBraid','Hair_M_UpdoMessyBun'):
  for suffix in ('Tangent','Attribute'):
   package=f'/Game/Grooms/{name}/{name}/{name}_CardsAtlas_{suffix}';texture=unreal.load_asset(package);assert texture
   file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset');before=hashlib.sha256(file.read_bytes()).hexdigest()
   row={'path':path(texture),'sha256_before':before}
   for n in ('srgb','compression_settings','mip_gen_settings','address_x','address_y','filter'):
    row[n]=str(texture.get_editor_property(n))
   row['sha256_after']=hashlib.sha256(file.read_bytes()).hexdigest();assert row['sha256_after']==before;REPORT['textures'].append(row)
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
