"""Bounded authored skin/hair correction on backed-up owned instances.

The previous skin tint exceeded one and rendered washed out. Hair census
exposes scatter up to two and strong specular despite dark base colour.
Preserve texture detail and masks; fresh rendered review remains mandatory.
"""
import datetime,hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
census=json.loads((OUT/'Child_Material_Roots.json').read_text());assert census['success']
eal=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary
backup=OUT/'Backups'/('FaceHair_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT={'success':False,'changes':[],'errors':[],
 'limits':'Authored material correction, preserving original archives and texture/mask bindings. Rendered face/hair acceptance pending.'}
skin={'WhiteBoy':(.76,.51,.37,1),'WhiteGirl':(.79,.55,.42,1)}
try:
 for row in census['materials']:
  identity=row['identity'];slot=row['slot'].lower()
  hair='HairShader' in row['parent_chain'][-1]
  skin_slot=identity in skin and ('skin' in slot or 'nails' in slot)
  if not (hair or skin_slot):continue
  path=row['parent_chain'][0].split('.')[0]
  assert path.startswith('/Game/Carnival/Characters/Children/'+identity+'/')
  asset=unreal.load_asset(path);assert isinstance(asset,unreal.MaterialInstanceConstant)
  file=ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset')
  copy=backup/(path.removeprefix('/Game/')+'.uasset');copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,copy)
  change={'asset':path,'identity':identity,'slot':row['slot'],'backup':str(copy),
          'before_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'parameters':[]}
  asset.modify()
  if skin_slot:
   name='Base Color Tint';before=mel.get_material_instance_vector_parameter_value(asset,name)
   mel.set_material_instance_vector_parameter_value(asset,name,unreal.LinearColor(*skin[identity]))
   stored=mel.get_material_instance_vector_parameter_value(asset,name)
   assert max(abs(a-b) for a,b in zip(stored.to_tuple(),skin[identity]))<.0001
   change['parameters'].append({'name':name,'before':before.to_tuple(),'after':stored.to_tuple()})
  if hair:
   names={str(x) for x in mel.get_scalar_parameter_names(asset)}
   for name,value in {'Scatter':.35,'Specular Multiplier':.2,'Specular Strength':.5,'Roughness Multiplier':1.3}.items():
    assert name in names,(path,name)
    before=mel.get_material_instance_scalar_parameter_value(asset,name)
    mel.set_material_instance_scalar_parameter_value(asset,name,value)
    stored=mel.get_material_instance_scalar_parameter_value(asset,name)
    assert abs(stored-value)<.0001
    change['parameters'].append({'name':name,'before':before,'after':stored})
  mel.update_material_instance(asset);assert eal.save_loaded_asset(asset)
  change['after_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();REPORT['changes'].append(change)
 assert REPORT['changes']
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'Child_Face_Hair_Material_Repair.json').write_text(json.dumps(REPORT,indent=2))
