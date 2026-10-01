"""Fresh-process verification of one saved stock head bake; does not save assets."""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
NAME=os.environ['CARNIVAL_HEAD_NAME']
OUT=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/NAME
saved=json.loads((OUT/'index.json').read_text());assert saved['success']
REPORT={'success':False,'errors':[],'head':NAME,'textures':[],'assets_saved':False}
try:
    source=ROOT/'Content'/(saved['source'].removeprefix('/Game/')+'.uasset')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==saved['source_sha256_before']
    for row in saved['saved_textures']:
        assert hashlib.sha256(Path(row['file']).read_bytes()).hexdigest()==row['sha256']
        texture=unreal.load_asset(row['asset']);assert isinstance(texture,unreal.Texture2D)
        assert texture.get_editor_property('srgb')==row['srgb']
        assert str(texture.get_editor_property('compression_settings'))==row['compression']
        image=OUT/(texture.get_name()+'_Reload.png')
        task=unreal.AssetExportTask();task.object=texture;task.filename=str(image)
        task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.TextureExporterPNG()
        assert unreal.Exporter.run_asset_export_task(task)
        assert image.read_bytes()==Path(row['png']).read_bytes(),row['asset']+' source pixels differ after reload'
        REPORT['textures'].append({'asset':row['asset'],'png':str(image),'export_identical':True})
    assert len(REPORT['textures'])==4
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
