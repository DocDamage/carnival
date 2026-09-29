"""Import the local Carnival expansion packs while preserving their package roots.

The user's source folder and archives are read-only. Existing destination folders
are reported and left untouched so interrupted or authored content is never
silently overwritten.
"""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(r"F:\Carnival")
CONTENT = ROOT / "Content"
REPORT = ROOT / "Saved/WorldExpansion/Source_Migration.json"

RAW_CONTENT = [
    (ROOT / "Assets/Untitled24493581f5aeV1/data/Content/Docks", CONTENT / "Docks", "shared docks pack"),
    (ROOT / "Assets/ModularSb35746afa6c6V1/data/Content/Sewer", CONTENT / "Sewer", "sewer pack"),
    (ROOT / "Assets/ModularSb35746afa6c6V1/data/Content/__ExternalActors__/Sewer", CONTENT / "__ExternalActors__/Sewer", "sewer external actors"),
    (ROOT / "Assets/ModularSb35746afa6c6V1/data/Content/__ExternalObjects__/Sewer", CONTENT / "__ExternalObjects__/Sewer", "sewer external objects"),
    (ROOT / "Assets/SciFiCredfa74d82e8f2V1/data/Content/SciFiWorld", CONTENT / "SciFiWorld", "research lab pack"),
]

ZIP_CONTENT = [
    (ROOT / "Assets/HauntedPrison.zip", "HAUNTED_PRISON"),
    (ROOT / "Assets/UnderwaterShip.zip", "UnderwaterShip"),
]


def copy_pack(source, destination, label):
    if not source.is_dir():
        raise FileNotFoundError(f"Missing {label} source: {source}")
    if destination.exists():
        return {"label": label, "source": str(source), "destination": str(destination), "state": "already_present"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, copy_function=shutil.copy2)
    files = [item for item in destination.rglob("*") if item.is_file()]
    return {
        "label": label,
        "source": str(source),
        "destination": str(destination),
        "state": "copied",
        "file_count": len(files),
        "bytes": sum(item.stat().st_size for item in files),
    }


def extract_project_pack(archive_path, package_root):
    if not archive_path.is_file():
        raise FileNotFoundError(f"Missing source archive: {archive_path}")
    prefixes = (
        f"Content/{package_root}/",
        f"Content/__ExternalActors__/{package_root}/",
        f"Content/__ExternalObjects__/{package_root}/",
    )
    extracted = []
    with zipfile.ZipFile(archive_path) as source_zip:
        for entry in source_zip.infolist():
            relative = entry.filename.replace("\\", "/")
            if not relative.startswith(prefixes) or entry.is_dir() or relative.endswith("/"):
                continue
            target = ROOT.joinpath(*relative.split("/"))
            resolved = target.resolve()
            if not resolved.is_relative_to(ROOT.resolve()):
                raise ValueError(f"Archive entry escapes the project root: {entry.filename}")
            if target.exists():
                if target.stat().st_size == entry.file_size:
                    continue
                raise FileExistsError(f"Refusing to overwrite an existing file with a different size: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with source_zip.open(entry) as packed, target.open("wb") as output:
                shutil.copyfileobj(packed, output, length=1024 * 1024)
            extracted.append({"path": str(target), "bytes": entry.file_size})
    if not any(item["path"].endswith(".uasset") or item["path"].endswith(".umap") for item in extracted):
        raise RuntimeError(f"No Unreal packages were extracted from {archive_path}")
    return {
        "label": package_root,
        "source": str(archive_path),
        "state": "extracted",
        "files": len(extracted),
        "bytes": sum(item["bytes"] for item in extracted),
        "external_actor_or_object_files": sum("__External" in item["path"] for item in extracted),
    }


def main():
    results = []
    for source, destination, label in RAW_CONTENT:
        results.append(copy_pack(source, destination, label))
    for archive_path, package_root in ZIP_CONTENT:
        results.append(extract_project_pack(archive_path, package_root))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    for result in results:
        print(result)
    print("Migration report:", REPORT)


if __name__ == "__main__":
    main()
