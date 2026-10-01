"""Read the saved crowd bake inputs; does not accept live poses or edit assets."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/CrowdAnimationInputSurvey_20260930';OUT.mkdir(parents=True,exist_ok=True)
PACKAGE='/Game/Carnival/Crowd/DA_CarnivalCrowdAnimations'
FILE=ROOT/'Content'/(PACKAGE.removeprefix('/Game/')+'.uasset')
REPORT={'success':False,'errors':[],'assets_saved':False,'animations':[],
        'limits':'Saved input metadata only. Actual actor/instanced sequences, bone motion, retargeting, foot contacts and pose transitions still require live observation.'}
def path(o):return o.get_path_name() if o else None
try:
    REPORT['sha256_before']=hashlib.sha256(FILE.read_bytes()).hexdigest()
    config=unreal.load_asset(PACKAGE);assert config
    REPORT['face_root_bone']=str(config.get_editor_property('FaceRootBoneName'))
    for item in config.get_editor_property('AnimationsToBake'):
        row={'name':str(item.get_editor_property('Name')),'merged':item.get_editor_property('bUseMergedAnimation'),
             'loop':item.get_editor_property('bLoop'),'root_motion':item.get_editor_property('bRootMotion'),'sources':{}}
        for field in ['BodyAnimSequence','FaceAnimSequence','MergedAnimSequence']:
            sequence=item.get_editor_property(field)
            row['sources'][field]={'asset':path(sequence),'length':sequence.get_play_length(),
                'skeleton':path(sequence.get_editor_property('skeleton'))} if sequence else None
        REPORT['animations'].append(row)
    REPORT['sha256_after']=hashlib.sha256(FILE.read_bytes()).hexdigest()
    assert REPORT['sha256_after']==REPORT['sha256_before']
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
