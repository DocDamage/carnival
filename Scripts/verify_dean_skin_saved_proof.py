"""Fresh-process texture reload and lossless exported-source comparison; no saves."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930'
saved=json.loads((OUT/'index.json').read_text());assert saved['success']
REPORT={'success':False,'errors':[],'textures':[],'assets_saved':False}
try:
    for row in saved['assets_saved']:
        file=Path(row['file']);assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256']
        texture=unreal.load_asset(row['asset']);assert texture,row['asset']
        assert isinstance(texture,unreal.Texture2D)
        assert texture.get_editor_property('srgb')==row['srgb']
        assert str(texture.get_editor_property('compression_settings'))==row['compression']
        image=OUT/(texture.get_name()+'_Reload.png')
        task=unreal.AssetExportTask();task.object=texture;task.filename=str(image)
        task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.TextureExporterPNG()
        assert unreal.Exporter.run_asset_export_task(task)
        # PNG export reads saved texture source pixels; identical files prove no data loss at save/reload.
        assert image.read_bytes()==Path(row['reference_png']).read_bytes(),row['asset']+' differs after reload'
        REPORT['textures'].append({'asset':row['asset'],'reload_png':str(image),'export_identical':True})
    assert len(REPORT['textures'])==4
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:
    (OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
