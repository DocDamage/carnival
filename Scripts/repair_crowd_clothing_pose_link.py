"""Repair only the owned actor's empty-material-map clothing pose link."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CrowdAcceptance/ClothingPoseLinkRepair_20260930';OUT.mkdir(parents=True,exist_ok=False)
ASSET='/Game/Carnival/Crowd/Actors/BP_CarnivalCrowdActor'
FILE=ROOT/'Content/Carnival/Crowd/Actors/BP_CarnivalCrowdActor.uasset'
STOCK=Path(r'C:\Program Files\UE_5.8\Engine\Plugins\MetaHuman\MetaHumanCrowd\Content\BP_CrowdActor.uasset')
CONFIG=ROOT/'Content/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig.uasset'
REPORT={'success':False,'errors':[],'asset':ASSET,'maps_modified':False,'appearance_assets_modified':False}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
try:
 REPORT['sha256_before']=digest(FILE);REPORT['stock_sha256_before']=digest(STOCK);REPORT['config_sha256_before']=digest(CONFIG)
 backup=OUT/'BeforePoseLink.uasset';shutil.copy2(FILE,backup);assert digest(backup)==REPORT['sha256_before'];REPORT['backup']=str(backup);save()
 bp=unreal.load_asset(ASSET);assert bp
 REPORT['graph_before']=list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
 result,error=unreal.CarnivalCrowdEditorLibrary.repair_crowd_clothing_pose_link(bp);assert result==1 and not error,error
 result,error=unreal.CarnivalCrowdEditorLibrary.repair_crowd_clothing_pose_link(bp);assert result==0 and not error,error
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);assert bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
 REPORT['graph_after']=list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
 assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
 REPORT['sha256_after']=digest(FILE);REPORT['stock_sha256_after']=digest(STOCK);REPORT['config_sha256_after']=digest(CONFIG)
 assert REPORT['stock_sha256_after']==REPORT['stock_sha256_before']
 assert REPORT['config_sha256_after']==REPORT['config_sha256_before']
 REPORT.update(success=True,limits='Saved actor execution-link repair; fresh reload, pooled appearance regression and rendered review still required. No GPU clothing fit or hair acceptance.')
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:save()
