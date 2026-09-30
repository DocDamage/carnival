"""Give owned child materials coherent skin/hair/clothing colours.

Supplied diffuse maps include flat 64px greys and source instances use white
tints. Preserve source archives, graph/texture detail and back up each changed
owned asset. This is an authored palette, not a claim of recovered source colour.
"""
import datetime,hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
source=json.loads((OUT/'Child_Guest_Blueprints.json').read_text());assert source['success']
PALETTES={
 'BlackGirl':{'skin':(.42,.21,.12,1),'hair':(.035,.022,.016,1),'top':(.65,.31,.035,1),'bottom':(.035,.075,.16,1),'shoe':(.075,.045,.028,1)},
 'WhiteBoy':{'skin':(.76,.51,.37,1),'hair':(.19,.075,.03,1),'top':(.035,.20,.42,1),'bottom':(.08,.11,.09,1),'shoe':(.055,.04,.032,1)},
 'WhiteGirl':{'skin':(.79,.55,.42,1),'hair':(.13,.065,.028,1),'top':(.35,.075,.11,1),'bottom':(.045,.10,.15,1),'shoe':(.085,.06,.045,1)},
 'BlackBoy':{'skin':(.34,.15,.077,1),'hair':(.025,.018,.014,1),'top':(.04,.27,.16,1),'bottom':(.16,.10,.045,1),'shoe':(.055,.045,.035,1)}}
REPORT={'success':False,'changes':[],'errors':[],'source_archives_modified':False,
 'limits':'Authored natural skin/hair and casual clothing palette on owned copies; requires fresh rendered appearance/gait/clipping acceptance. Original grey source colours are preserved in backups.'}
eal=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary
backup=OUT/'Backups'/('Palette_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
seen=set()

def category(slot):
 name=slot.lower()
 if 'skin' in name or 'nails' in name:return 'skin'
 if 'hair' in name or 'scalp' in name or 'transparency' in name:return 'hair'
 if 'shirt' in name or name=='top' or name.startswith('top_'):return 'top'
 if any(s in name for s in ('short','pant','trouser')):return 'bottom'
 if any(s in name for s in ('shoe','sandal')):return 'shoe'
 if any(s in name for s in ('bracelet','buckle','necklace','strandthree')):return 'metal'
 if 'tongue' in name:return 'tongue'
 if 'teeth' in name:return 'teeth'
 if 'eyelash' in name:return 'hair'
 return None

for child in source['children']:
 identity=child['identity'];namespace='/Game/Carnival/Characters/Children/'+identity+'/'
 try:
  mesh=unreal.load_asset(child['mesh'])
  for slot in mesh.materials:
   kind=category(str(slot.material_slot_name))
   if not kind:continue
   asset=slot.material_interface;path=asset.get_path_name().split('.')[0]
   if path in seen:continue
   seen.add(path);assert path.startswith(namespace)
   value=PALETTES[identity].get(kind,{'metal':(.65,.42,.16,1),'tongue':(.65,.13,.15,1),'teeth':(2.1,2.0,1.85,1)}.get(kind))
   assert value
   file=ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset');old_sha=hashlib.sha256(file.read_bytes()).hexdigest()
   copy=backup/(path.removeprefix('/Game/')+'.uasset');copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,copy)
   asset.modify()
   if isinstance(asset,unreal.MaterialInstanceConstant):
    if 'Base Color Tint' not in [str(x) for x in mel.get_vector_parameter_names(asset)]:
     raise RuntimeError('Missing colour tint parameter '+path)
    old=mel.get_material_instance_vector_parameter_value(asset,'Base Color Tint')
    # Installed UE5.8 MaterialEditingLibrary.cpp performs the update but never
    # sets its bool result true. Verify the actual stored value instead.
    mel.set_material_instance_vector_parameter_value(asset,'Base Color Tint',unreal.LinearColor(*value))
    mel.update_material_instance(asset)
    stored=mel.get_material_instance_vector_parameter_value(asset,'Base Color Tint')
    assert max(abs(a-b) for a,b in zip([stored.r,stored.g,stored.b,stored.a],value))<.0001
    before=[old.r,old.g,old.b,old.a]
   else:
    assert identity=='BlackBoy' and isinstance(asset,unreal.Material)
    tint=None
    for name in mel.get_vector_parameter_names(asset):
     if str(name)=='Base Color Tint':
      node_path=eal.get_metadata_tag(asset,'CarnivalChildTintNode')
      assert node_path,'Existing colour parameter has no owned-node provenance '+path
      tint=unreal.load_object(None,node_path)
      assert isinstance(tint,unreal.MaterialExpressionVectorParameter)
    before=None
    if not tint:
     base=mel.get_material_property_input_node(asset,unreal.MaterialProperty.MP_BASE_COLOR);assert base
     output=mel.get_material_property_input_node_output_name(asset,unreal.MaterialProperty.MP_BASE_COLOR)
     tint=mel.create_material_expression(asset,unreal.MaterialExpressionVectorParameter,-350,-400)
     tint.set_editor_property('parameter_name','Base Color Tint')
     eal.set_metadata_tag(asset,'CarnivalChildTintNode',tint.get_path_name())
     multiply=mel.create_material_expression(asset,unreal.MaterialExpressionMultiply,-100,-150)
     assert mel.connect_material_expressions(base,output,multiply,'A')
     assert mel.connect_material_expressions(tint,'RGB',multiply,'B')
     assert mel.connect_material_property(multiply,'',unreal.MaterialProperty.MP_BASE_COLOR)
    tint.set_editor_property('default_value',unreal.LinearColor(*value));mel.recompile_material(asset)
   assert eal.save_loaded_asset(asset)
   REPORT['changes'].append({'identity':identity,'slot':str(slot.material_slot_name),'category':kind,
    'asset':path,'before_tint':before,'authored_linear_tint':value,'backup':str(copy),
    'before_sha256':old_sha,'after_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 except Exception:REPORT['errors'].append(identity+': '+traceback.format_exc())
REPORT['success']=not REPORT['errors'] and all(any(x['identity']==c['identity'] for x in REPORT['changes']) for c in source['children'])
(OUT/'Child_Material_Palette.json').write_text(json.dumps(REPORT,indent=2))
