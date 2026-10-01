"""Read-only: label families and bounds per in-scope campaign level; no saves."""
import collections,hashlib,json,re,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance/RegionFurnishings_20260930';OUT.mkdir(parents=True,exist_ok=False)
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
LEVELS=['L_CoastalMansionApproach','L_HauntedMansionConnected','L_IndustrialSlums_DistrictFinal','L_CarnivalWorldExpansion_Prison',
 'L_CarnivalWorldExpansion_LabA','L_CarnivalWorldExpansion_LabB','L_CarnivalWorldExpansion_Sewers','L_CarnivalWorldExpansion_DocksNorth_Layout',
 'L_CarnivalWorldExpansion_DocksEast','L_CarnivalWorldExpansion_Shipwreck','L_CarnivalWorldExpansion_Atlantis','LV_Carnival']
R={'success':False,'errors':[],'assets_saved':False,'levels':{}}
try:
 before=hashlib.sha256(MAPFILE.read_bytes()).hexdigest()
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 for name in LEVELS:
  mine=[a for a in actors if '/'+name+'.'+name+':' in a.get_path_name()]
  fam=collections.Counter(re.sub(r'[\d_]+$','',a.get_actor_label()) for a in mine)
  lo=[1e12]*3;hi=[-1e12]*3;rows=[]
  for a in mine:
   o,e=a.get_actor_bounds(False)
   if e.length()>20000 or e.length()<1:continue
   for i,(c,x) in enumerate(zip(o.to_tuple(),e.to_tuple())):lo[i]=min(lo[i],c-x);hi[i]=max(hi[i],c+x)
   rows.append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
  R['levels'][name]={'actors':len(mine),'bounds_min':lo,'bounds_max':hi,'families':fam.most_common(120),'actors_list':rows}
 assert hashlib.sha256(MAPFILE.read_bytes()).hexdigest()==before
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
