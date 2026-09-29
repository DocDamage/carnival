# Interior and water vehicle continuation — 2026-09-29

All Unreal launches and builds are serialized by the root agent. These scripts
must not start while another editor, cook or build is running.

## Verified observations

`Saved/WorldExpansion/InteriorCameraAcceptance/Roundtrips.json` passed the mansion
mission-room route and hospital entrance, including continuous walking returns
and 12 actual player-camera endpoint checks each. It did not pass Sewer start
height or the Atlantis endpoint. This is not full interior-room acceptance.

The harness now records Sewer handoff floor probes. Do not substitute the old
stairs final capsule height at a different XY: that older harness stops within
170 cm of its endpoint. Atlantis's final intended floor was corrected to the
R12 walkway upper face (-1782.5 cm), and endpoints must settle on ground before
the existing height checks run. These harness corrections need execution.

`Saved/WorldExpansion/WaterVehicleAcceptance/main_PlacementSurvey.json` completed
successfully. It contains **zero CarnivalBoat and zero CarnivalHovercraft**
placements. All six dock collision positive controls passed. NorthDock surfaces
are around world Z635; adjacent collision traces frequently hit Landscape2 at
Z-260. A WaterBodyRiver exists, but its actor bounds are not a usable water-depth
measurement. Do not author a boat at deck height or assume deep water here.

## Ready scripts

- `Scripts/playtest_interior_camera_roundtrips.py`: set
  `CARNIVAL_INTERIOR_CASES=sewer_corridor,atlantis_hall` and a fresh
  `CARNIVAL_INTERIOR_REPORT` for the corrected endpoints and floor diagnostics.
- `Scripts/prepare_hospital_room_candidate_routes.py`: generated three longer
  hospital candidate routes from the old floor graph. The source report omitted
  edge-blocker details, so these are candidates, not proven paths. Select
  `hospital_corridor_west,hospital_corridor_east,hospital_corridor_south` in the
  same pawn harness. Their lengths are approximately 44, 66 and 94 m.
- `Scripts/survey_dock_water_depth.py`: Water plugin surface/normal/velocity/depth
  query, same-body overlap below the surface, separate terrain-depth traces,
  NorthDock hover lane floor samples and real candidate mesh bounds. Read-only
  PIE; no extra native helper required. Engine source confirms the exposed
  `get_water_surface_info_at_location` uses the UE5.8 safe query API.
- `Scripts/author_integrated_water_vehicles.py`: requires a concrete
  `Saved/WorldExpansion/WaterVehicleAcceptance/PlacementPlan.json` tied to the
  placement survey SHA. Project-owned copied levels only; backs each up; refuses
  unrelated same-name actors; tags owned vehicles, optional boarding decks and
  handling activity. Boat water plane is absolute world Z, auto detection off,
  explicit surveyed water bounds on. `PlacementPlan.json` now contains a concrete
  NorthDock hovercraft and handling activity, backed by 45 successful pier floor
  probes. It is ready for authoring; no vehicle map save is yet confirmed here.
- `Scripts/playtest_integrated_water_vehicle_lifecycle.py`: requires successful
  authoring with matching plan SHA and measured straight drive lane >=10 m.
  Actual saved pawn walks to contextual mount, drives out, reverses continuously,
  ordinarily unloads to safe ground and walks back. No spawned fixture vehicles
  and no mid-test teleports. Direct control APIs do not accept physical input,
  the whole activity course, every shoreline or rendered presentation.

## Native change awaiting shared build/tests

`CarnivalBoat.h/.cpp` now support opt-in world XY water bounds and minimum keel
clearance. All eight rotated hull corners must fit. Center/corner Visibility
traces reject shallow solid ground, avoiding the WaterBodyCollision object's
WorldStatic blocking response. Moves sample <=40 cm corner travel so long
frames cannot jump a boundary. Invalid regions fail closed; legacy default off.

`CarnivalBoatBoundaryTests.cpp` adds
`Carnival.Vehicles.BoatSurveyedWaterBoundary`: legacy behavior, invalid region,
bow/rotation bounds, shallow/deep ground, powered stop and reverse recovery.
Compilation and execution are owned by root; do not claim these passed until
the shared report confirms it.

## Subsequent depth survey

`DockWaterDepth.json` passed: 632 query points, 353 same-body overlaps, 18 samples
with collision-measured depth above 150 cm. The real surface is -240 cm. Most
near-dock floor depths are only 20 cm despite the Water plugin reporting nominal
depth 150 cm, so use the independent collision measurement. A deeper basin lies
near x[-50000,-46000], y[-59000,-56000]; terrain there is approximately 163–867 cm
below the water. This may support a boat without changing terrain.

Run the same depth script with `CARNIVAL_WATER_DEPTH_AREA=boat_berth` for a dense
100 cm grid around the deeper basin. It writes `DockWaterBerth.json`, preserving
the original survey hash used by the hovercraft plan. A project-owned descending
boarding ramp and whole-hull water region must follow this survey, then actual
pawn boarding/return/unloading must pass.

## Hospital interaction gap

The existing door audit includes 48 Blueprint door assemblies among 131 actors
matching door/frame names. No exposed open/close/interact API was found by that
audit. `TryContextInteract` has no generic hospital door path. Run the longer
candidate routes first to identify actual blocking leaves; do not tag all door
frames or rotate arbitrary meshes. A narrow native interaction component and
project-copy hinge authoring should target measured leaves only.
