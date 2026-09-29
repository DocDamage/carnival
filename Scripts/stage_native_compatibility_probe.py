"""Stage new native code against a preserved prior cook for compatibility testing.

This is deliberately not final content acceptance. Only immutable cooked
containers are hard-linked; logs, configuration and binaries are independent.
"""
import datetime, json, os, shutil
from pathlib import Path

root=Path(r'F:\Carnival')
prior=json.loads((root/'Saved/WorldExpansion/Route_Refresh_Package.json').read_text())
assert prior['success']
source=Path(prior['launch_directory']).resolve()
binary=root/'Binaries/Win64/CarnivalGame.exe'
assert binary.is_file()
destination=root/'Saved/Packages'/('NativeCompatibility_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
def copy(source_file, dest_file):
    if Path(source_file).suffix.lower() in ('.pak','.ucas','.utoc'):
        os.link(source_file,dest_file)
        return dest_file
    return shutil.copy2(source_file,dest_file)
shutil.copytree(source,destination,copy_function=copy,
                ignore=shutil.ignore_patterns('Saved','*.log','*.pdb'))
shutil.copy2(binary,destination/'CarnivalGame/Binaries/Win64/CarnivalGame.exe')
report={'success':True,'launch_directory':str(destination),'source_archive':str(source),
        'binary':str(binary),'binary_mtime':binary.stat().st_mtime,
        'scope':'New native executable with prior cooked content; not current map, asset or full-game acceptance.'}
(root/'Saved/WorldExpansion/Native_Compatibility_Stage.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
