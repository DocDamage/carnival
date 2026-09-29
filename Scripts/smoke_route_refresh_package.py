"""Launch the refreshed DX12 archive and observe it for two minutes after map load."""
import datetime
import json
import os
import re
import subprocess
import time
from pathlib import Path

import psutil

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/WorldExpansion'
probe = os.environ.get('CARNIVAL_NATIVE_COMPATIBILITY_PROBE') == '1'
candidate = os.environ.get('CARNIVAL_COMPLETION_CANDIDATE') == '1'
assert not (probe and candidate), 'Choose one package report'
package = json.loads((OUT / ('Completion_Candidate_Package.json' if candidate else 'Native_Compatibility_Stage.json' if probe else 'Route_Refresh_Package.json')).read_text())
if not package.get('success'):
    raise RuntimeError('Fresh package did not complete successfully')
archive = Path(package['launch_directory'])
log = archive / 'RouteRefresh_DX12_Startup.log'
if log.exists():
    log.rename(log.with_name(log.stem + '_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.log'))
report_path = OUT / ('Completion_Candidate_Smoke.json' if candidate else 'Native_Compatibility_Smoke.json' if probe else 'Route_Refresh_Package_Smoke.json')
args = [str(archive / 'CarnivalGame.exe'), '-dx12', '-RenderOffscreen',
        '-windowed', '-ResX=1280', '-ResY=720', '-nosplash', '-unattended',
        '-abslog=' + str(log)]
report = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'command': args, 'runtime_log': str(log), 'success': False,
          'scope': 'Offscreen DX12 startup and process survival; not visual, input, mission, or performance acceptance.'}
if probe:
    report['scope'] = package['scope']
process = subprocess.Popen(args, cwd=archive, creationflags=subprocess.CREATE_NO_WINDOW)
owned = {process.pid: psutil.Process(process.pid)}
start = time.monotonic()
ready = None
try:
    while time.monotonic() - start < 420:
        for parent in list(owned.values()):
            try:
                for child in parent.children(recursive=True):
                    owned[child.pid] = child
            except psutil.NoSuchProcess:
                pass
        text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        loaded = 'Load map complete /Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival' in text
        if loaded and ready is None:
            ready = time.monotonic()
        alive = [p.pid for p in owned.values() if p.is_running()]
        if not alive:
            report['unexpected_exit'] = True
            break
        if ready is not None and time.monotonic() - ready >= 120:
            report['observed_alive_after_map_load_seconds'] = round(time.monotonic() - ready, 2)
            report['alive_pids_at_end'] = alive
            break
        time.sleep(2)
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    patterns = {'fatal_error': 'Fatal error', 'bad_import_index': 'Bad import index',
                'critical_error': '=== Critical error: ===', 'assertion_failure': 'Assertion failed:',
                'unhandled_exception': 'Unhandled Exception',
                'metahuman_missing_template': 'Could not find template object',
                'invalid_shader_maps': 'invalid ShaderMap',
                'missing_root_physics': 'Could not find root physics body'}
    report['counts'] = {k: text.count(v) for k, v in patterns.items()}
    report['runtime_archetype_restored'] = 'Carnival: restored UE 5.8 MetaHuman collection runtime archetype.' in text
    report['map_loaded'] = ready is not None
    report['max_logged_frame'] = max([int(n) for n in re.findall(r'\]\[\s*(\d+)\]', text)] or [0])
    report['success'] = bool(report.get('observed_alive_after_map_load_seconds', 0) >= 120
                             and not report.get('unexpected_exit')
                             and not any(report['counts'][k] for k in ('fatal_error', 'critical_error', 'assertion_failure', 'bad_import_index', 'unhandled_exception')))
finally:
    # Stop only processes launched by this helper, preserving unrelated editor/game sessions.
    stopped = []
    for child in reversed(list(owned.values())):
        try:
            if child.is_running():
                child.terminate()
                stopped.append(child.pid)
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(list(owned.values()), timeout=10)
    report['intentional_smoke_stop_pids'] = stopped
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report_path.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['success'] else 1)
