"""Create a guarded owned actor template; keep stock plugin content unchanged."""
import datetime, hashlib, json, shutil, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/CrowdAcceptance/ActorBeginPlayRepair_20260930'
OUT.mkdir(parents=True, exist_ok=True)
BACKUP = OUT/'Backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True, exist_ok=False)
SOURCE = Path(r'C:\Program Files\UE_5.8\Engine\Plugins\MetaHuman\MetaHumanCrowd\Content\BP_CrowdActor.uasset')
ACTOR = '/Game/Carnival/Crowd/Actors/BP_CarnivalCrowdActor'
CONFIG = '/Game/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig'
REPORT = {'success': False, 'errors': [], 'assets': [], 'maps_modified': False,
          'density_changed': False, 'appearance_changed': False, 'plugin_content_modified': False}
def digest(file): return hashlib.sha256(file.read_bytes()).hexdigest()
def backup(package):
    file = ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.uasset')
    row = {'package': package, 'new_asset': not file.exists()}
    if file.exists():
        target = BACKUP/file.name; shutil.copy2(file, target)
        row.update(backup=str(target), sha256_before=digest(file))
        assert digest(target) == row['sha256_before']
    REPORT['assets'].append(row)
try:
    REPORT['stock_actor_sha256_before'] = digest(SOURCE)
    backup(ACTOR); backup(CONFIG)
    actor_file = ROOT/'Content/Carnival/Crowd/Actors/BP_CarnivalCrowdActor.uasset'
    bp = unreal.load_asset(ACTOR) if actor_file.exists() else None
    if not bp:
        stock = unreal.load_asset('/MetaHumanCrowd/BP_CrowdActor'); assert stock
        bp = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('BP_CarnivalCrowdActor', '/Game/Carnival/Crowd/Actors', stock)
    assert bp
    REPORT['before_graph'] = list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
    result, error = unreal.CarnivalCrowdEditorLibrary.guard_crowd_actor_begin_play(bp)
    assert result in (0, 1) and not error, error
    repeated, error = unreal.CarnivalCrowdEditorLibrary.guard_crowd_actor_begin_play(bp)
    assert repeated == 0 and not error, error
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    REPORT['after_graph'] = list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(ACTOR)
    assert cls
    config = unreal.load_asset(CONFIG); assert config
    visual = next(t for t in config.get_editor_property('config').get_editor_property('traits')
                  if t.get_class().get_name() == 'MetaHumanMassCrowdVisualizationTrait')
    appearances = [a.get_path_name() for a in visual.get_editor_property('character_instances')]
    params, lod = str(visual.get_editor_property('params')), str(visual.get_editor_property('lod_params'))
    REPORT['actor_slots_before'] = {}
    allowed = {'/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C', cls.get_path_name()}
    for name in ('high_res_template_actor', 'low_res_template_actor'):
        old = visual.get_editor_property(name)
        assert old and old.get_path_name() in allowed, 'Unexpected actor template'
        REPORT['actor_slots_before'][name] = old.get_path_name()
        visual.set_editor_property(name, cls)
    assert [a.get_path_name() for a in visual.get_editor_property('character_instances')] == appearances
    assert str(visual.get_editor_property('params')) == params and str(visual.get_editor_property('lod_params')) == lod
    assert unreal.EditorAssetLibrary.save_loaded_asset(config, False)
    REPORT.update(character_instances=appearances, actor_class=cls.get_path_name())
    for row in REPORT['assets']:
        row['sha256_after'] = digest(ROOT/'Content'/Path(row['package'].removeprefix('/Game/')).with_suffix('.uasset'))
    REPORT['stock_actor_sha256_after'] = digest(SOURCE)
    assert REPORT['stock_actor_sha256_after'] == REPORT['stock_actor_sha256_before']
    REPORT.update(success=True, limits='Guarded actor initialization and saved template configuration. Actual delayed appearance assignment, full live representation, silhouette/lighting and animation acceptance remain required.')
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT, indent=2))
