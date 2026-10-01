"""Create /Game/Carnival/World/Materials/Water/M_CarnivalUnderwaterPP: the follow camera's underwater view.

Scene colour fades to FogColor with view distance (FogKeepPerMetre ^ metres), and everything above the water
surface (SurfaceZ) is fully fogged, which hides the open space and terrain underside above flooded interiors.
Parameters are driven per water volume by ACarnivalPlayerCharacter. Saves only the new material."""
import json,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\CharacterRepairs\UnderwaterPP_v3_20261001');OUT.mkdir(parents=True,exist_ok=False)
PKG='/Game/Carnival/World/Materials/Water';NAME='M_CarnivalUnderwaterPP'
R={'success':False,'errors':[]}
ML=unreal.MaterialEditingLibrary
try:
 import shutil
 src=Path(r'F:\Carnival\Content\Carnival\World\Materials\Water')/(NAME+'.uasset')
 if src.exists():
  shutil.copy2(src,OUT/(NAME+'.v2_backup.uasset'))
  assert unreal.EditorAssetLibrary.delete_asset(PKG+'/'+NAME)
 assert not unreal.EditorAssetLibrary.does_asset_exist(PKG+'/'+NAME)
 m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME,PKG,unreal.Material,unreal.MaterialFactoryNew())
 m.set_editor_property('material_domain',unreal.MaterialDomain.MD_POST_PROCESS)
 m.set_editor_property('blendable_location',unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF if hasattr(unreal.BlendableLocation,'BL_SCENE_COLOR_BEFORE_DOF') else unreal.BlendableLocation.BL_BEFORE_TONEMAPPING)
 E=lambda cls,x,y:ML.create_material_expression(m,cls,x,y)
 def C(a,ao,b,bi):
  assert ML.connect_material_expressions(a,ao,b,bi),(a.get_class().get_name(),ao,b.get_class().get_name(),bi)
 scene=E(unreal.MaterialExpressionSceneTexture,-1200,0);scene.set_editor_property('scene_texture_id',unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
 rgb=E(unreal.MaterialExpressionComponentMask,-950,0)
 for k in ('r','g','b'):rgb.set_editor_property(k,True)
 C(scene,'Color',rgb,'')
 depth=E(unreal.MaterialExpressionSceneTexture,-1200,250);depth.set_editor_property('scene_texture_id',unreal.SceneTextureId.PPI_SCENE_DEPTH)
 dmask=E(unreal.MaterialExpressionComponentMask,-950,250);dmask.set_editor_property('r',True);C(depth,'Color',dmask,'')
 metres=E(unreal.MaterialExpressionDivide,-750,250);C(dmask,'',metres,'A');metres.set_editor_property('const_b',100.0)
 keep=E(unreal.MaterialExpressionScalarParameter,-750,400);keep.set_editor_property('parameter_name','FogKeepPerMetre');keep.set_editor_property('default_value',0.92)
 pw=E(unreal.MaterialExpressionPower,-550,300);C(keep,'',pw,'Base');C(metres,'',pw,'Exp')
 fog=E(unreal.MaterialExpressionOneMinus,-380,300);C(pw,'',fog,'')
 wp=E(unreal.MaterialExpressionWorldPosition,-750,550)
 sz=E(unreal.MaterialExpressionScalarParameter,-750,680);sz.set_editor_property('parameter_name','SurfaceZ');sz.set_editor_property('default_value',100000.0)
 dz=E(unreal.MaterialExpressionSubtract,-550,560);C(wp,'Z',dz,'A');C(sz,'',dz,'B')
 # Fully fogged within 0.5 m above the surface: hides open space / terrain above flooded water.
 sc=E(unreal.MaterialExpressionMultiply,-420,560);C(dz,'',sc,'A');sc.set_editor_property('const_b',0.02)
 above=E(unreal.MaterialExpressionSaturate,-300,560);C(sc,'',above,'')
 total=E(unreal.MaterialExpressionMax,-200,400);C(fog,'',total,'A');C(above,'',total,'B')
 col=E(unreal.MaterialExpressionVectorParameter,-380,100);col.set_editor_property('parameter_name','FogColor');col.set_editor_property('default_value',unreal.LinearColor(0.012,0.075,0.095,1))
 colrgb=E(unreal.MaterialExpressionComponentMask,-260,100)
 for k in ('r','g','b'):colrgb.set_editor_property(k,True)
 C(col,'',colrgb,'')
 lerp=E(unreal.MaterialExpressionLinearInterpolate,-150,150);C(rgb,'',lerp,'A');C(colrgb,'',lerp,'B');C(total,'',lerp,'Alpha')
 assert ML.connect_material_property(lerp,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 ML.recompile_material(m)
 unreal.EditorAssetLibrary.save_asset(PKG+'/'+NAME,False)
 R['blendable_location']=str(m.get_editor_property('blendable_location'))
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
