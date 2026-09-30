"""Stage supplied child sources independently; never overwrite shared rigs.

This is an offline source inventory/extraction, not Unreal migration or visual
acceptance. Purchased sources and staged copies remain local.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'F:\3D Characters\Metahuman Downloads\Children')
OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
SOURCES=[('BlackGirl','Rigged 3D Black Girl Character Game Animation Ready'),
         ('WhiteBoy','Rigged 3D White Boy Character Game Animation Ready'),
         ('WhiteGirl','Rigged 3D White Girl Character Game Animation Ready'),
         ('BlackBoy','Rigged 3D Black Boy Character Game Animation Ready')]
report={'success':False,'sources':[],'project_content_modified':False,
        'visual_acceptance':False,'rig_animation_clothing_acceptance':False,
        'limits':'Independent staged source projects preserve differing same-named skeletons. Requires namespace-safe migration, rig validation, animation, capsule/contact/seat fitting and rendered review.'}
OUT.mkdir(parents=True,exist_ok=True)
for identity,folder in SOURCES:
    directory=SOURCE/folder
    archives=([directory/'unreal_project_clean.zip'] if identity!='BlackBoy' else
              [directory/'fbx_clean.zip',directory/'textures.zip'])
    row={'identity':identity,'source_folder':str(directory),'archives':[]}
    for archive in archives:
        destination=(OUT/identity/('Unreal' if 'unreal' in archive.name else archive.stem)).resolve()
        entries=[]
        with ZipFile(archive) as zipped:
            for item in zipped.infolist():
                relative=PurePosixPath(item.filename)
                if relative.is_absolute() or '..' in relative.parts or '\\' in item.filename:
                    raise RuntimeError('Unsafe archive path '+item.filename)
                target=destination.joinpath(*relative.parts).resolve()
                if not target.is_relative_to(destination): raise RuntimeError('Archive escaped staging directory')
                if item.is_dir(): continue
                blob=zipped.read(item)
                digest=hashlib.sha256(blob).hexdigest()
                if target.exists():
                    if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
                        raise RuntimeError('Refusing to overwrite different staged source '+str(target))
                else:
                    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(blob)
                if item.filename.endswith('.uproject'):
                    row['staged_project']=str(target)
                    row['source_engine_association']=json.loads(blob.decode('utf-8-sig')).get('EngineAssociation')
                if item.filename.endswith('/Characters/Mannequin_UE4/Meshes/SK_Mannequin_Skeleton.uasset'):
                    row['shared_skeleton_sha256']=digest
                entries.append({'name':item.filename,'sha256':digest,'bytes':len(blob)})
        row['archives'].append({'source':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                                'staged_root':str(destination),'files':entries})
    report['sources'].append(row)
report['success']=len(report['sources'])==4
(OUT/'SourceManifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'success':report['success'],'sources':[{k:v for k,v in row.items() if k!='archives'} for row in report['sources']],
                  'files':sum(len(a['files']) for s in report['sources'] for a in s['archives'])},indent=2))
