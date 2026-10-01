import json,unreal
ML=unreal.MaterialEditingLibrary
m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_TmpProbeInputs','/Game/Carnival/Tmp',unreal.Material,unreal.MaterialFactoryNew())
R={}
for cls in (unreal.MaterialExpressionPower,unreal.MaterialExpressionLinearInterpolate,unreal.MaterialExpressionSaturate,unreal.MaterialExpressionSubtract,unreal.MaterialExpressionMultiply,unreal.MaterialExpressionMax,unreal.MaterialExpressionDivide,unreal.MaterialExpressionOneMinus,unreal.MaterialExpressionComponentMask):
 e=ML.create_material_expression(m,cls,0,0)
 R[cls.__name__]=[str(x) for x in ML.get_material_expression_input_names(e)]
for cls in (unreal.MaterialExpressionSceneTexture,unreal.MaterialExpressionWorldPosition):
 e=ML.create_material_expression(m,cls,0,0)
 R[cls.__name__+'_out']=[str(x) for x in ML.get_material_expression_output_names(e)] if hasattr(ML,'get_material_expression_output_names') else 'n/a'
open(r'F:\Carnival\Saved\CharacterRepairs\MaterialInputNames_20261001.json','w').write(json.dumps(R,indent=1))
