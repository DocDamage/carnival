"""Sample a small landscape patch for the authored industrial-slum district."""
import json
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Source/Slum_Terrain_Heightfield.json"
world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/IndustrialSlums/Levels/L_DemoScene")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
landscape = next((a for a in eas.get_all_level_actors() if a.get_class().get_name() == "Landscape"), None)
if not landscape:
    raise RuntimeError("Source landscape actor was not found")

x0, x1, y0, y1, step = -20000.0, -10000.0, 0.0, 16000.0, 200.0
xs = [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
ys = [y0 + i * step for i in range(int((y1 - y0) / step) + 1)]
points = [unreal.Vector(x, y, 0.0) for y in ys for x in xs]
heights = unreal.CarnivalWorldEditorLibrary.sample_landscape_heights(landscape, points)
if len(heights) != len(points):
    raise RuntimeError(f"Landscape returned {len(heights)} heights for {len(points)} points")
data = {
    "source": "/Game/IndustrialSlums/Levels/L_DemoScene",
    "grid_cm": {"x_min": x0, "x_max": x1, "y_min": y0, "y_max": y1, "step": step},
    "xs": xs,
    "ys": ys,
    "heights": [float(h) for h in heights],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
unreal.log(f"INDUSTRIAL_SLUMS_TERRAIN_SAMPLED {len(points)}")
unreal.SystemLibrary.quit_editor()
