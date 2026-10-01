"""Read clothing slot declarations and counts; no assembly or asset changes."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/CrowdClothingSlotSurvey_20260930';OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'collections':[],'assets_saved':False,
 'limits':'Declared slot/item counts only. Empty virtual slots and ownership fallback are diagnosis leads, not a reproduced cause of missing body surfaces.'}
try:
 for group in range(1,7):
  name='DA_CarnivalCrowd_G'+str(group)+'_FINAL2';package='/Game/Carnival/Crowd/Collections/'+name
  file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset');before=hashlib.sha256(file.read_bytes()).hexdigest()
  collection=unreal.load_asset(package);assert collection
  row=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(collection));assert row.get('slots')
  row['slots'].sort(key=lambda r:r['slot']);row['sha256_before']=before;row['sha256_after']=hashlib.sha256(file.read_bytes()).hexdigest()
  assert row['sha256_before']==row['sha256_after'];REPORT['collections'].append(row)
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
