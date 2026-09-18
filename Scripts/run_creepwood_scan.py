"""Headless driver for CarnivalMetaHuman editor automation.

Loads the Creepwood showcase map, prepares the /Game/Carnival content folders,
scans the level for ride candidates, writes reports, then quits the editor.

Run from a command line:
    UnrealEditor.exe "CarnivalGame.uproject" -stdout -unattended -nop4 -nullrhi
        -nosplash -ExecutePythonScript="<this file>" -ExecCmds="quit"
"""
import json
import os
import traceback

import unreal

LOG = []
KIT_SCRIPTS = r"E:\Carvival\CarnivalGame\Plugins\CarnivalMetaHumanKit\Scripts"
PROJECT_SCRIPTS = r"E:\Carvival\CarnivalGame\Scripts"


def log(msg):
    LOG.append(msg)
    unreal.log_warning("CarnivalKit: " + msg)


def run_script(path):
    with open(path, encoding="utf-8") as fh:
        code = fh.read()
    # Fresh module-level namespace so top-level functions can reference each other
    # (avoids the exec-inside-a-function scoping pitfalls with closures).
    exec(compile(code, path, "exec"), {})


def write_report(ok):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "CarnivalKit")
    os.makedirs(out_dir, exist_ok=True)
    payload = {"success": ok, "log": LOG}
    with open(os.path.join(out_dir, "HeadlessScanReport.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main():
    ok = False
    try:
        map_path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
        log("Loading map: " + map_path)
        loaded = unreal.EditorLevelLibrary.load_level(map_path)
        log("load_level -> %s" % loaded)

        # Prepare content folders.
        try:
            script = os.path.join(KIT_SCRIPTS, "prepare_content_folders.py")
            run_script(script)
        except Exception:
            log("prepare_content_folders failed:\n" + traceback.format_exc())

        # Scan for ride candidates.
        try:
            script = os.path.join(KIT_SCRIPTS, "scan_creepwood_level.py")
            run_script(script)
        except Exception:
            log("scan_creepwood_level failed:\n" + traceback.format_exc())

        # Dump ride component hierarchies.
        try:
            script = os.path.join(PROJECT_SCRIPTS, "dump_ride_components.py")
            run_script(script)
        except Exception:
            log("dump_ride_components failed:\n" + traceback.format_exc())

        ok = True
    except Exception:
        log("Driver failed:\n" + traceback.format_exc())
    finally:
        write_report(ok)
        log("done (success=%s)" % ok)

    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass


main()
