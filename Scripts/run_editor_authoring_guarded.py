"""Run synchronous editor authoring with an error report and guaranteed exit.

Set CARNIVAL_EDITOR_SCRIPT to a project Scripts filename. Do not use for PIE
callbacks, whose asynchronous lifetime intentionally outlasts script execution.
"""
import json, os, traceback
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_dir()).resolve()
target=(root/'Scripts'/os.environ['CARNIVAL_EDITOR_SCRIPT']).resolve()
if target.parent != root/'Scripts' or target.suffix!='.py':
    raise ValueError('Expected a Python file directly inside project Scripts')
report={'script':str(target),'success':False}
try:
    namespace={'__name__':'__main__','__file__':str(target)}
    exec(compile(target.read_text(encoding='utf-8'),str(target),'exec'),namespace)
    outcome=namespace.get('REPORT',namespace.get('report'))
    if isinstance(outcome,dict) and (outcome.get('errors') or outcome.get('success') is False):
        raise RuntimeError('Authoring reported failures: '+str(outcome.get('errors',outcome.get('error','success=false'))))
    report['success']=True
except Exception:
    report['error']=traceback.format_exc()
    unreal.log_error(report['error'])
finally:
    path=root/'Saved/HauntedDollIntegration'/(target.stem+'_guard.json')
    path.write_text(json.dumps(report,indent=2))
    unreal.SystemLibrary.quit_editor()
