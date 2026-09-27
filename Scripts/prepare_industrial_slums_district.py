"""Extract only the 100 x 160 m slum district needed by the connected road.

Actors are moved from the source map into a new streaming-level package inside
the editor session, then only that new package is saved. The 1.8 GB vendor demo
map and its day/night sublevels are never saved or changed.
"""
import hashlib
import json
import traceback
from collections import Counter
from pathlib import Path
import unreal
import sys

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import OUT, SLUM_LEVEL, SLUM_CROP

SOURCE = "/Game/IndustrialSlums/Levels/L_DemoScene"
SOURCE_FILE = ROOT / "Content/IndustrialSlums/Levels/L_DemoScene.umap"
DEST_FILE = ROOT / ("Content" + SLUM_LEVEL.replace("/Game", "").replace("/", "\\") + ".umap")
REPORT = OUT / "Slums_District_Build.json"
OUT.mkdir(parents=True, exist_ok=True)

report = {
    "source": SOURCE,
    "destination": SLUM_LEVEL,
    "source_sha256_before": hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest(),
    "crop_cm": SLUM_CROP,
    "phase": "loading_source",
    "actors_moved": 0,
    "class_counts": {},
}


def save_report():
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


def fail(exc):
    report["phase"] = "failed"
    report["error"] = repr(exc)
    report["traceback"] = traceback.format_exc()
    save_report()
    unreal.log_error("INDUSTRIAL_SLUMS_DISTRICT_FAILED: " + repr(exc))


try:
    if DEST_FILE.exists():
        raise FileExistsError("Refusing to replace an existing authored level: " + str(DEST_FILE))

    world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
    if not world or not world.get_path_name().startswith(SOURCE + "."):
        raise RuntimeError("Could not load the source slum map")

    # Keep the source map's persistent level only; all vendor day/night layouts
    # remain untouched and are omitted from the curated district.
    for level in list(unreal.EditorLevelUtils.get_levels(world)):
        if not level.get_path_name().startswith(SOURCE + "."):
            if not unreal.EditorLevelUtils.remove_level_from_world(level):
                raise RuntimeError("Could not detach source demo sublevel " + level.get_path_name())

    x0, x1, y0, y1 = SLUM_CROP
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    excluded = Counter()
    source_persistent_prefix = SOURCE + "."
    skip_classes = {
        "GroupActor", "HDRIBackdrop_C", "PlayerStart", "CameraActor", "CineCameraActor",
        "LevelSequenceActor", "DirectionalLight", "SkyAtmosphere", "SkyLight",
        "ExponentialHeightFog", "PostProcessVolume", "RuntimeVirtualTextureVolume",
    }
    def collect_source_crop():
        found = []
        for actor in eas.get_all_level_actors():
            actor_class = actor.get_class().get_name()
            owner = actor.get_level().get_path_name()
            if not owner.startswith(source_persistent_prefix):
                continue
            if actor_class in skip_classes:
                continue
            if actor_class == "Landscape":
                found.append(actor)
                continue
            location = actor.get_actor_location()
            if x0 <= location.x <= x1 and y0 <= location.y <= y1:
                found.append(actor)
        return found

    selected = []
    for actor in actors:
        actor_class = actor.get_class().get_name()
        owner = actor.get_level().get_path_name()
        if not owner.startswith(source_persistent_prefix):
            excluded["nonpersistent_level"] += 1
        elif actor_class in skip_classes:
            excluded[actor_class] += 1
        elif actor_class != "Landscape":
            location = actor.get_actor_location()
            if not (x0 <= location.x <= x1 and y0 <= location.y <= y1):
                excluded[actor_class] += 1
    selected = collect_source_crop()

    if not selected:
        raise RuntimeError("The selected district crop contained no source actors")
    report["source_actor_count"] = len(actors)
    report["selected_actor_count"] = len(selected)
    report["excluded_actor_count"] = sum(excluded.values())
    report["excluded_class_counts"] = dict(excluded)
    report["class_counts"] = dict(Counter(a.get_class().get_name() for a in selected))
    report["phase"] = "creating_streaming_level"
    save_report()

    streaming = unreal.EditorLevelUtils.create_new_streaming_level(
        unreal.LevelStreamingAlwaysLoaded, SLUM_LEVEL, False
    )
    if not streaming:
        raise RuntimeError("Could not create the district streaming level")
    streaming.set_editor_property("should_be_loaded", True)
    streaming.set_editor_property("should_be_visible", True)

    report["phase"] = "moving_selected_actors"
    save_report()
    target_count = len(selected)
    moved = 0
    del selected, actors
    batch_size = 250
    batch_index = 0
    while moved < target_count:
        remaining = collect_source_crop()
        if not remaining:
            break
        # Unreal's Python bridge occasionally loses the concrete object
        # property type when a long list comprehension feeds a native
        # TArray<AActor*>. Build an explicitly typed Unreal array per batch.
        batch = unreal.Array.cast(unreal.Actor, remaining[:batch_size])
        count = unreal.EditorLevelUtils.move_actors_to_level(
            batch, streaming, False, False
        )
        if count != len(batch):
            raise RuntimeError(f"Moved {count} of {len(batch)} actors in batch {batch_index}")
        moved += count
        report["actors_moved"] = moved
        save_report()
        unreal.log(f"INDUSTRIAL_SLUMS_DISTRICT_MOVE {moved}/{target_count}")
        batch_index += 1
        del batch, remaining

    unreal.EditorLevelUtils.make_level_current(streaming)
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Saving the extracted district level failed")
    report["phase"] = "verifying_saved_level"
    report["saved_file_exists"] = DEST_FILE.exists()
    report["saved_file_bytes"] = DEST_FILE.stat().st_size if DEST_FILE.exists() else 0
    save_report()

    # Close the unsaved vendor map and open the new package as a standalone map
    # to verify that the moved actors really landed in its PersistentLevel.
    district_world = unreal.EditorLoadingAndSavingUtils.load_map(SLUM_LEVEL)
    district_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    reopened_class_counts = Counter(a.get_class().get_name() for a in district_actors)
    expected_class_counts = Counter(report["class_counts"])
    missing_class_counts = {
        cls: {"expected": count, "reopened": reopened_class_counts.get(cls, 0)}
        for cls, count in expected_class_counts.items()
        if reopened_class_counts.get(cls, 0) < count
    }
    report["reopened_world"] = district_world.get_path_name() if district_world else None
    report["reopened_actor_count"] = len(district_actors)
    report["reopened_class_counts"] = dict(reopened_class_counts)
    report["class_counts_missing"] = missing_class_counts
    report["note"] = (
        "Grouped/attached vendor actors transfer as a hierarchy; the editor move API's returned count "
        "does not equal the reopened actor count. Verification requires every selected class count, "
        "the unchanged source hash, and a nonempty saved district."
    )
    report["source_sha256_after"] = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()
    if report["source_sha256_after"] != report["source_sha256_before"]:
        raise RuntimeError("The original vendor source map changed on disk")
    if not district_actors or missing_class_counts:
        raise RuntimeError(f"The saved district is missing selected actor classes: {missing_class_counts}")
    report["phase"] = "complete"
    save_report()
    unreal.log(f"INDUSTRIAL_SLUMS_DISTRICT_COMPLETE actors={target_count}")
except Exception as exc:
    fail(exc)
finally:
    unreal.SystemLibrary.quit_editor()
