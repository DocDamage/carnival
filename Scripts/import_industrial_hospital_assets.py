"""Copy the locally licensed Industrial Slums and Hospital packs into Content.

The authored routes use the packs' original /Game paths. Source archives under
Assets remain untouched. The sample third-person map is excluded because it
is not part of the connected environment and its external actor package paths
overlap the project's existing third-person sample.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(r"F:\Carnival")
CONTENT = ROOT / "Content"
PACKS = [
    (
        ROOT / "Assets/ModularS16743c69c8b4V1/data/Content/IndustrialSlums",
        CONTENT / "IndustrialSlums",
        True,
    ),
    (
        ROOT / "Assets/Apocalypc5d977999b35V3/data/Content/Hospital_Meshingun",
        CONTENT / "Hospital_Meshingun",
        False,
    ),
]
REPORT_DIR = ROOT / "Saved/IndustrialHospital"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

copy_plan = []
conflicts = []
for source_root, destination_root, exclude_third_person in PACKS:
    if not source_root.is_dir():
        raise FileNotFoundError(f"Missing source pack: {source_root}")
    for source in source_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        if exclude_third_person and relative.parts[0] == "ThirdPerson":
            continue
        destination = destination_root / relative
        if destination.exists():
            conflicts.append(str(destination))
        copy_plan.append((source, destination))

if conflicts:
    raise FileExistsError("Refusing to overwrite existing assets: " + ", ".join(conflicts[:20]))

copied = []
total_bytes = 0
for source, destination in copy_plan:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    copied.append(str(destination.relative_to(ROOT)))
    total_bytes += source.stat().st_size
    if len(copied) % 250 == 0:
        print(f"Copied {len(copied)} files", flush=True)

report = {
    "files_copied": len(copied),
    "bytes_copied": total_bytes,
    "sources": [str(source) for source, _, _ in PACKS],
    "excluded": ["IndustrialSlums/ThirdPerson/**"],
    "files": copied,
}
(REPORT_DIR / "Asset_Import.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Copied {len(copied)} files ({total_bytes / 1024**3:.2f} GiB)", flush=True)
