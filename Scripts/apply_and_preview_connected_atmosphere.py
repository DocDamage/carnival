"""Apply focused, backed-up corrections, then render the saved connected world."""
import json
import math
import runpy
import sys
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
try:
    for script, report in (
        ("apply_connected_night_backdrops.py", "Night_Backdrop_Correction.json"),
        ("correct_hospital_sodium_lights.py", "Sodium_Light_Correction.json"),
    ):
        runpy.run_path(str(ROOT / "Scripts" / script))
        result = json.loads((ROOT / "Saved/IndustrialHospital" / report).read_text())
        if not result["success"]:
            raise RuntimeError("Correction failed; inspect " + report)
    sys.path.insert(0, str(ROOT / "Scripts"))
    import mansion_route_config as coast
    extra = []
    for name, local in (("05_Coastal_Bridge", (-10200, -50, 635)),
                        ("06_Mansion_Approach", (44500, -7000, 1090))):
        position = coast.world_point(local)
        yaw = math.radians(coast.COAST_YAW)
        target = (position[0] + 2000 * math.cos(yaw), position[1] + 2000 * math.sin(yaw), position[2])
        extra.append((name, position, target))
    runpy.run_path(str(ROOT / "Scripts/capture_industrial_hospital_connected.py"), init_globals={
        "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/CorrectedAtmosphere",
        "CAPTURE_EXTRA_CASES": extra,
    })
except Exception:
    error = traceback.format_exc()
    (ROOT / "Saved/IndustrialHospital/Atmosphere_Application_Error.txt").write_text(error)
    unreal.log_error(error)
    unreal.SystemLibrary.quit_editor()
