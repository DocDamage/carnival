# Carnival Integration Status

Status of integrating the `CarnivalMetaHumanKit` into the CarnivalMetaHuman Unreal project
built on the purchased Creepwood Wonderland environment.

## Environment

- Unreal Engine: **5.8.2** (`C:\Program Files\UE_5.8`, `++UE5+Release-5.8`, changelist 56702186)
- Toolchain: Visual Studio 2022 BuildTools 14.44 + Windows 10 SDK 10.0.26100
- Platform: Windows (x64)
- Project: `F:\Carnival\CarnivalGame.uproject`
- Game module: `CarnivalGame` (minimal C++ host module)
- Plugin location: `F:\Carnival\Plugins\CarnivalMetaHumanKit\`

## Creepwood content

- Source (VaultCache extract): `C:\EpicVaultCache\VaultCache\THECARNIc9ee0c490dc7V4\data\Content\Creepwood_Carnival_Meshingun`
- Migrated into project: `F:\Carnival\Content\Creepwood_Carnival_Meshingun` (plain copy; object paths preserved under `/Game/Creepwood_Carnival_Meshingun`)
- Asset count: ~2263 `.uasset`/`.umap` files, ~15.7 GB

### Showcase map

- `/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.LV_Carnival`
- Configured as `EditorStartupMap` / `GameDefaultMap` in `Config/DefaultEngine.ini`.

### Additional maps

- `LV_Cinematic`, `Lv_LightingDay`, `Lv_LightingNight`, `Lv_LightingNightSnow`
- `LV_Rope_Splines`, `LV_UnMerged_Rope_Splines`, `LV_VFX_and_SFX`
- Overview: `LV_Overview`, `LV_Rides_Overview`, `LV_Xmas_AddonOverview`

## Plugins

Enabled in `CarnivalGame.uproject`:

- `CarnivalPopulation` (this kit)
- `MetaHumanCrowd`, `MassAI`, `MassCrowd`
- `StateTree`, `ZoneGraph`, `SmartObjects`

All verified present in the installed UE 5.8 engine. Their transitive dependencies
(e.g. `MetaHumanCharacter`, `MetaHumanSDK`, `MassEntity`, `MassGameplay`) are resolved
automatically by UBT from each plugin's `.uplugin` descriptor.

## Build / compile state

- `CarnivalPopulation` plugin **compiles cleanly** against UE 5.8.2 (Development Editor, Win64).
- Full editor target (`CarnivalGameEditor`) **builds and links successfully** with the full
  MetaHuman/Mass/StateTree/ZoneGraph/SmartObjects stack enabled.
- Visual Studio solution generated at `CarnivalGame.sln` / `CarnivalGame.slnx`.

### Compile errors fixed

1. `CarnivalRideQueueComponent.cpp` — `TArray<TObjectPtr<ACarnivalQueuePoint>>::Sort`
   failed to compile. In UE 5.8 `TArray<TObjectPtr<T>>::Sort` dereferences elements before
   invoking the predicate, so the comparator must accept `const ACarnivalQueuePoint&`
   (raw object references), not `const TObjectPtr<ACarnivalQueuePoint>&`.
   Fix: changed the sort lambda parameter types and removed the now-redundant null checks
   (elements are validated for null before being added to the array).

No other UHT/UBT/deprecation errors were encountered. Public class names and
Blueprint-facing APIs are unchanged.

## Creepwood ride inventory (discovered from asset names + Blueprint string tables)

All ride Blueprints live under `Environment/Blueprint/Ride/` and inherit from a shared
parent `Structure/BP_Rides_Parent`. Color/material variants are child Blueprints in
`Environment/Blueprint/Ride/Instance/`.

| Ride | Base Blueprint | Motion hint (discovered) |
|---|---|---|
| Ferris Wheel | `BP_FerrisWheel_Ride_01a` | `RotatingMovementComponent` (`RotatingMovement`) |
| Carousel | `BP_Carousel_Ride_01a` | rotation + `S_HorseMovementLimit` (horse bob) |
| Pirate Ship | `BP_PirateShip_Ride_01a` | `C_PirateShip` component (pendulum swing) |
| Swing | `BP_Swing_Ride_01a` | rotation |
| Teapot | `BP_Teapot_Ride_01a` | rotation |
| Flying Bobs | `BP_FlyingBobs_Ride_01a` | `S_SplineRailContainer` spline rail |
| Bumper Cars | `BP_BumperCars_Ride_01a` | (dedicated arena gameplay — defer) |
| Balloon Tower | `BP_BalloonTower_Ride_01a` | `C_HotairBalloonFloat` + `E_BalloonRotationType` |
| Clown Ride | `BP_Clown_Ride_01a` | rotation |
| Circus | `BP_Circus_Ride_01a` | — |
| Haunted House | `BP_HauntedHouse_Ride_01a` | — (walk-through) |
| Hot Air Balloon | `BP_HotairBalloon_Ride_01a` | `C_HotairBalloonFloat` |

### Shared ride structure (in `Ride/Structure/`)

- `BP_Rides_Parent` — shared ride base class (holds animation/timeline/control logic).
- `E_RideState` — ride phase enum: `Starting`, `Started`, `Stopping`, `Stopped`.
- `S_SeatRotation` — per-seat rotation data.
- `S_ArrayOfStaticMeshComponents`, `S_RotationLerpContainer`, `S_LocationLerpContainer`,
  `S_CustomLerpSpeed`, `S_SplineRailContainer`, `S_MaterialInstanceRecord`,
  `S_MaterialCustomization`, `S_MaterialIdentity`, `S_MaterialParameterOptions`,
  `S_MaterialOptionLocal`, `S_AudioFadeOut`.
- Custom components: `C_HotairBalloonFloat`, `C_PirateShip`, `C_StartFromZero`.
- Enums: `E_BalloonRotationType`, `E_MaterialIdentityType`.

### Ferris Wheel (first integration candidate) — discovered internals

`BP_FerrisWheel_Ride_01a` contains (from Blueprint string table):

- Motion: `RotatingMovementComponent` (`RotatingMovement` / `RotatingMovement_GEN_VARIABLE`).
- Cabins/gondolas: `Local_currentCabin`, `Local_currentCabinSM`, `Local_leftSphereCabins`,
  `Local_rightSphereCabins`, `Local_sortedCombinedCabins`, `Local_sortedLeftSphereCabins`,
  `Local_sortedRightSphereCabins`, `Local_currentMasterComponent`, `Local_tempSMs`.
- Cabin physics swing: `PhysicsConstraintComponent`, `PhysicalAnimationComponent`.
- Sorting helper: `SortComponentBasedOnDistanceToZ` (orders cabins).
- Ride control functions: `StartRide`, `StopRide`, `TurnOnRide`, `TurnOffRide`, `ReceiveBeginPlay`.
- Static meshes: `SM_Ferris_Wheel_Platform_Enter2`, `SM_Ladder_01`…`SM_Ladder_19`.
- Materials: `MI_FerrisWheel_Bulb`, `MI_FerrisWheel_Platform_Floor`, `MI_FerrisWheel_TextBG`.

## Current status vs milestones

### Done this pass

- [x] Plugin integrated into `Plugins/CarnivalMetaHumanKit/`.
- [x] Plugin compiles cleanly in real UE 5.8.2 project.
- [x] Full plugin dependency chain (MetaHuman/Mass/StateTree/ZoneGraph/SmartObjects) validated.
- [x] VS solution generated.
- [x] Creepwood content located, inventoried, and migrated into project `Content/`.
- [x] Actual ride Blueprint names + component hints identified via binary string analysis.
- [x] Showcase map configured as startup map.

### Requires Unreal Editor interaction (next tasks)

These cannot be completed headlessly and must be performed in the editor:

1. Open `LV_Carnival` and confirm it loads cleanly.
2. Run `Scripts/prepare_content_folders.py` to create the `/Game/Carnival/...` hierarchy.
3. Run `Scripts/scan_creepwood_level.py` to dump placed actors into
   `Saved/CarnivalKit/CreepwoodRideCandidates.json`.
4. For the Ferris Wheel: create a **derived** Blueprint (child of `BP_FerrisWheel_Ride_01a`
   or its in-map `Instance/` variant) and add:
   - `UCarnivalRideControllerComponent`
   - `UCarnivalRideMotionComponent` (call `SetMotionSource` with the rotating wheel/cabin root)
   - `UCarnivalRideQueueComponent`
   - one `UCarnivalRideSeatComponent` per gondola seat (parented to the gondola mesh),
     each with `SeatId`, `RestraintType`, `PassengerOffset`, hand/foot IK targets.
5. Place `ACarnivalQueuePoint` actors along the physical queue with matching `RideId`.
6. Set `ExitTransform` to a safe load/unload point.
7. Wire the existing `StartRide`/`StopRide` timeline calls to
   `SetRidePhase(Running)` / `SetRidePhase(Unloading)` + `UnboardAllPassengers()`.
8. Create the first MetaHuman passenger actor with `UCarnivalRidePassengerComponent`
   implementing `ICarnivalPassengerInterface`.
9. Create the shared ride AnimBP (`Ride_Enter/Ride_Idle/Ride_Grip/.../Ride_Exit` layers,
   hand/foot IK from seat transforms) per `Docs/ANIMATION_BLUEPRINT.md`.
10. Author the MetaHuman Collection/Instances + Mass spawner for the roaming crowd.

## Known issues

- Engine is installed at a non-standard path (`C:\Program Files\UE_5.8`); `EngineAssociation`
  is set to `"5.8"`. If the Epic Launcher is not aware of this install, open the project via
  command line or register the engine in the Launcher before double-clicking the `.uproject`.
- `E_RideState` and the ride control function names were extracted from Blueprint binary
  strings and must be confirmed in the Blueprint editor before relying on them.

## Next tasks (priority order)

1. Open `LV_Carnival` in the editor and verify content/map integrity.
2. Run the two editor Python scripts; inspect ride candidates.
3. Wire the Ferris Wheel end-to-end (derived BP + controller/motion/queue/seats).
4. Create the first MetaHuman passenger + shared ride AnimBP.
5. Prove one full ride cycle (board → run → react → unboard).
6. Generalize to Carousel / Swing / Pirate Ship / Teapot.
7. Add Mass crowd + ZoneGraph midway routing + StateTree behavior.

---

## Headless editor validation (performed this pass)

The editor was launched headlessly (`-nullrhi -unattended -ExecutePythonScript`) and:

- **Opened cleanly with no plugin errors** (full MetaHuman/Mass/StateTree/ZoneGraph/SmartObjects/Python stack loaded).
- **Loaded `LV_Carnival`** successfully (`load_level -> True`).
- **Ran `prepare_content_folders.py`** (created `/Game/Carnival/...` folders).
- **Ran `scan_creepwood_level.py`** → wrote `Saved/CarnivalKit/CreepwoodRideCandidates.json`
  (45 candidates; 25 ride Blueprint actors dumped).
- **Ran `dump_ride_components.py`** → wrote `Saved/CarnivalKit/RideComponents.json`
  (full component hierarchies with mobility, relative transforms and attach parents).

Automation entry point: `Scripts/run_creepwood_scan.py` (project-level driver). It runs the
kit scripts via a fresh module namespace to avoid Python `exec` scoping pitfalls.

### Automation fixes made

- `scan_creepwood_level.py`: replaced a generator-expression (`any(word in haystack ...)`)
  with an explicit loop — the genexpr failed with `NameError` when the script was exec'd
  inside a function.
- New `Scripts/dump_ride_components.py`: dumps per-ride component hierarchy.

### Key discovery — ride placement and motion drivers

- **Ferris Wheel and Carousel are NOT placed in `LV_Carnival`.** They live in the
  `Lv_LightingDay`, `Lv_LightingNight` and `Lv_LightingNightSnow` maps (which the editor
  world surfaces as additional levels).
- Rides present in `LV_Carnival`: Pirate Ship, Swing, Teapot, Flying Bobs, Balloon Tower,
  Clown Ride, Circus, Haunted House, Bumper Cars, Hot Air Balloons.
- Two motion drivers observed across Creepwood rides:
  1. `RotatingMovementComponent` — Ferris Wheel (`RotatingMovement`), Swing
     (`RotatingMovement_Anchor` + `RotatingMovement_Sphere`), Teapot
     (`RotatingMovement_Anchor` + `RotatingMovement_Cup1..6`), Balloon Tower
     (`RotatingMovement_Anchor` + `RotatingMovement_Seat1..8`), Clown Ride
     (`RotatingMovement_Anchor` + `RotatingMovement_Seat1..5`).
  2. Timeline animation — Pirate Ship (`PirateShipAnimation`), Carousel (`Carousel`),
     Flying Bobs (`FlyingBobAnimation`), Circus (`Circus`).
- `UCarnivalRideMotionComponent::SetMotionSource` must therefore point at the *moving
  SceneComponent* (e.g. `SM_Mainboat_PirateRide` for the Pirate Ship, `MainAnchor`/`Swings`
  for the Swing, the rotating wheel/cabins for the Ferris Wheel), not a generic root.

### First-ride recommendation (revised)

Because the Ferris Wheel and Carousel are absent from the showcase map, start with the
**Swing** (`BP_Swing_Ride_01a`, `RotatingMovement_Anchor` + suspended chairs) or the
**Pirate Ship** (`BP_PirateShip_Ride_01a`, Timeline pendulum + row benches). See
`Docs/FIRST_RIDE_WIRING.md`.

---

## Ride Blueprint automation (performed this pass)

Programmatic (headless) ride wiring is now proven working via `Scripts/wire_ride.py`.
It derives a **reversible child Blueprint** from the vendor ride (purchased assets are
never modified) and adds the CarnivalKit components.

### Derived Blueprints created (in `/Game/Carnival/Rides/`)

- `BP_Swing_Carnival` (child of `BP_Swing_Ride_01a`) — **fully wired**:
  - 1× `CarnivalRideControllerComponent`
  - 1× `CarnivalRideMotionComponent`
  - 1× `CarnivalRideQueueComponent`
  - 34× `CarnivalRideSeatComponent` (one per `SM_Swing_Chair` mesh, parented to the chair
    so seats inherit rotation + chain swing; each with a unique `SeatId`).
- `BP_PirateShip_Carnival` (child of `BP_PirateShip_Ride_01a`) — derived (components/seat
  wiring to be applied; the Pirate Ship uses row benches, not discrete chair meshes).

### Automation API (UE 5.8 Python) notes

- Create child Blueprint: `AssetToolsHelpers.get_asset_tools().create_asset(...)` +
  `BlueprintFactory` with `parent_class` set to the parent's `generated_class()`.
- Add/remove components on a Blueprint: `SubobjectDataSubsystem` with
  `k2_gather_subobject_data_for_blueprint`, `add_new_subobject(AddNewSubobjectParams(...))`,
  `rename_subobject`, `delete_subobject(actor_handle, component_handle, blueprint)`.
- Read a subobject's object/name from its handle via
  `unreal.SubobjectDataBlueprintFunctionLibrary` (`get_data`, `get_associated_object`,
  `is_actor`, `is_root_component`, `get_parent_handle`).
- Reference implementation: `Engine/Plugins/Experimental/Toolsets/EditorToolset/.../actor.py`.

### Remaining manual steps for the Swing (see `FIRST_RIDE_WIRING.md`)

1. In `BP_Swing_Carnival`, call `CarnivalRideMotion` → `SetMotionSource` with `MainAnchor`
   in `BeginPlay`.
2. Set `CarnivalRideController` → `RideId = "Swing"`, `ExitTransform`, and the same for
   `CarnivalRideQueue`.
3. Tune `PassengerOffset` / hand IK targets per seat (defaults are sensible placeholders).
4. Place `CarnivalQueuePoint` actors along the physical queue.
5. Hook the vendor `StartRide`/`StopRide` timeline to the controller's `SetRidePhase`.
6. Create the MetaHuman passenger + shared ride AnimBP + IK.



