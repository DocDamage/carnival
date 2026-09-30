"""Namespace supplied rigs inside disposable projects, then migrate dependencies.

Run only in a MigrationWorkspace source project; original staged files remain
immutable. Destination conflicts fail preflight and never overwrite assets. This establishes asset
transfer only, not character presentation/animation/seat acceptance.
"""
import hashlib,json,os,time,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival')
BASE=ROOT/'Saved/CharacterAcceptance/ChildSources'
IDENTITY=os.environ['CARNIVAL_CHILD_SOURCE']
SOURCE_ROOTS={'BlackGirl':'chlid_femele_test1','WhiteBoy':'child_test_2','WhiteGirl':'child_female_test_2'}
if IDENTITY not in SOURCE_ROOTS: raise ValueError('Unsupported child project')
project=Path(unreal.Paths.project_dir()).resolve()
expected=(BASE/'MigrationWorkspace'/IDENTITY).resolve()
if project!=expected: raise RuntimeError('Migration must run in disposable source project')
prefix='/Game/Carnival/Characters/Children/'+IDENTITY
destination=ROOT/'Content/Carnival/Characters/Children'/IDENTITY
report={'success':False,'identity':IDENTITY,'project':str(project),'namespace':prefix,
        'started_epoch':time.time(),'errors':[],'renamed':[],'assets':[],
        'visual_animation_clothing_acceptance':False}
try:
    if destination.exists(): raise RuntimeError('Destination already exists; inspect previous migration instead of overwriting')
    library=unreal.EditorAssetLibrary
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(synchronous_search=True)
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=False,
        include_hard_package_references=True,include_searchable_names=False,
        include_soft_management_references=False,include_hard_management_references=False)
    original_mesh='/Game/'+SOURCE_ROOTS[IDENTITY]+'/mesh/unreal_file'
    mesh_path=prefix+'/'+SOURCE_ROOTS[IDENTITY]+'/mesh/unreal_file'
    # Move only the body's hard dependency closure. Source UE5 demo ControlRig
    # pose animations are unrelated and cannot safely be renamed wholesale.
    report['reused_namespace']=library.does_asset_exist(mesh_path)
    pending=[] if report['reused_namespace'] else [original_mesh]
    original_packages=set()
    while pending:
        package=pending.pop()
        if package in original_packages or not package.startswith('/Game/'): continue
        original_packages.add(package)
        pending.extend(str(x) for x in registry.get_dependencies(package,options))
    renames=[]
    for package in sorted(original_packages):
        data=list(registry.get_assets_by_package_name(package))
        if len(data)!=1:
            raise RuntimeError('Expected one dependency asset in '+package+': '+str(data))
        asset=data[0].get_asset()
        if not asset: raise RuntimeError('Cannot load child dependency '+package)
        new=prefix+'/'+package.removeprefix('/Game/')
        directory,name=new.rsplit('/',1)
        renames.append(unreal.AssetRenameData(asset,directory,name))
        report['renamed'].append({'old':package,'new':new})
    if renames and not unreal.AssetToolsHelpers.get_asset_tools().rename_assets(renames):
        raise RuntimeError('Failed child dependency namespace rename')
    if not library.save_directory(prefix,only_if_is_dirty=False,recursive=True):
        raise RuntimeError('Failed saving namespaced source assets')
    mesh=unreal.load_asset(mesh_path)
    if not isinstance(mesh,unreal.SkeletalMesh): raise RuntimeError('Missing supplied skeletal body '+mesh_path)
    skeleton=mesh.get_editor_property('skeleton')
    if not skeleton or not skeleton.get_path_name().startswith(prefix+'/'):
        raise RuntimeError('Body still references a shared source skeleton')
    report['mesh']=mesh_path; report['skeleton']=skeleton.get_path_name()
    # Hard package references must all remain inside this child's namespace.
    registry.scan_paths_synchronous([prefix],force_rescan=True)
    pending=[mesh_path]; packages=set()
    while pending:
        package=pending.pop()
        if package in packages: continue
        if package.startswith('/Game/') and not package.startswith(prefix+'/'):
            raise RuntimeError('Unresolved source dependency '+package)
        if not package.startswith('/Game/'): continue
        packages.add(package)
        pending.extend(str(x) for x in registry.get_dependencies(package,options))
    # Migrate the verified hard closure explicitly, avoiding unrelated demo maps
    # and soft references from the source project's third-person template.
    for package in packages:
        for extension in ('.uasset','.uexp','.ubulk'):
            path=ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix(extension)
            if path.exists(): raise RuntimeError('Destination conflict '+str(path))
    # UE5.8's new migrator treats CANCEL as unconditional cancellation even
    # without conflicts (AssetTools.cpp SetupPublicAssetPackagesMigrationData).
    # Explicit preflight plus SKIP preserves existing files under any race.
    migration=unreal.MigrationOptions(prompt=False,ignore_dependencies=True,
        asset_conflict=unreal.AssetMigrationConflict.SKIP)
    # The new instanced-package migrator collides with Find-in-Blueprint cache
    # entries for the already loaded wrinkle AnimBP. The supported legacy file
    # migration preserves the UE-renamed/resaved packages without reloading a
    # duplicate Blueprint. This override is confined to this disposable process.
    editor_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(editor_world,'AssetTools.UseNewPackageMigration 0')
    report['migration_backend']='UE5.8 AssetTools legacy package copy, process-local override'
    unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(sorted(packages),str(ROOT/'Content'),migration)
    for package in sorted(packages):
        path=ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.uasset')
        if not path.exists(): raise RuntimeError('Migration omitted '+package)
        report['assets'].append({'package':package,'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    report['success']=True
except Exception:
    report['errors'].append(traceback.format_exc())
    unreal.log_error(report['errors'][-1])
finally:
    report['finished_epoch']=time.time()
    (BASE/(IDENTITY+'_Migration.json')).write_text(json.dumps(report,indent=2))
    unreal.SystemLibrary.quit_editor()
