# Carnival World Expansion — Layout and Connections

Updated 2026-09-29. The supplied map is used as a route and mood reference. Its compass rose, decorative scale, illustrated island boundary, and building sizes were not used as surveyed world coordinates.

## Active world and region maps

The active project is F:\Carnival\CarnivalGame.uproject, Unreal Engine 5.8.3. The main gameplay map is /Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.

The root map references the expansion as Always Loaded sublevels. Their transforms and the authored entry anchors below are recorded in Saved/WorldExpansion/World_Connection.json and Saved/WorldExpansion/Region_Authoring.json.

| Region | Package | Root-map transform (cm; yaw) | Authored role |
|---|---|---|---|
| Docks North | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout | (-55000, -55000, 600); 0 deg | Compact irregular waterfront using the shared Docks/VOL2_Powell library. |
| Prison | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison | (-24829.059, -33605.033, -1037.206); -45 deg | Main surface junction; connections to both docks, Lab, and Sewers. |
| Research Lab A | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA | (-42097.963, -7043.717, 600); -57 deg | Lab entry/control room. World entry anchor: (-41000, -8000, 600). |
| Research Lab B | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB | (-43649.095, -4655.183, 600); -57 deg | Secondary research room; its open front meets Lab A's west opening (corrected 2026-09-30, see below). |
| Docks East | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast | (70000, 15000, 600); 0 deg | Longer, ordered quay using the same imported pack as Docks North. |
| Sewers | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers | (-27100, -12290, -1800); 0 deg | Lower corridor and connection to Atlantis. Sewer entry from the stair: (-27000, -12500, -1800). |
| Atlantis Ruins | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Atlantis | (-13000, -11000, -1800); 0 deg | Ancient interior beyond the sewer tunnel. |
| Shipwreck | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck | (-6033.089, -10010, -2108.649); 0 deg | Terminal wreck environment; its supplied ship and set-dressing sublevels are retained. |
| Generated connectors | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout | (0, 0, 0); 0 deg | Shared outer route, Lab route, Prison service walk/stairs, and sealed lower tunnels. |

The root map still references the existing Carnival, wetlands/train bridge, mansion, Hospital, and Slums levels. The single linked connector level is L_CarnivalWorldExpansion_Connections_Layout; an older partial L_CarnivalWorldExpansion_Connections map is not linked.

## Required graph

| ID | Connection | Authored route | Approximate authored length | Current status |
|---|---|---|---:|---|
| R01 | Carnival ↔ Coastal Train Bridge | Existing wetlands approach to the bridge's west threshold | 224.51 m | Preserved; prior traversal evidence covers the combined Carnival-to-Mansion route, not this new endpoint split. |
| R02 | Coastal Train Bridge ↔ Mansion | Existing bridge east threshold, wetlands trail, and driveway | 226.57 m | Preserved; prior combined route evidence exists. |
| R03 | Mansion ↔ Docks North | Shared OuterRoute spine | 551.98 m | Authored; player traversal pending. |
| R04 | Docks North ↔ Prison | Shared OuterRoute spine | 736.67 m | Authored; player traversal pending. |
| R05 | Prison ↔ Docks East | Shared OuterRoute spine | 1342.37 m | Authored; player traversal pending. |
| R06 | Docks East ↔ Hospital | Shared OuterRoute spine | 359.18 m | Authored to the existing Hospital entry; player traversal pending. |
| R07 | Hospital ↔ Slums | Existing industrial hospital road | 793.44 m estimate | Existing connected content retained; endpoint split and player traversal pending. |
| R08 | Slums ↔ Carnival | Existing industrial hospital road from the Slums south street interface to the opposite Carnival gate | 610.52 m estimate | Existing connected content retained; endpoint split and player traversal pending. |
| R09 | Prison ↔ Research Lab | Separate surface spur | 205.14 m | Authored; player traversal pending. |
| R10 | Prison ↔ Sewers | Service walk plus reversible interior stair | 67.12 m walk + 65 m stair; 24 m drop | Authored as 120 steps; collision and traversal pending. |
| R11 | Sewers ↔ Atlantis Ruins | Sealed passage | 82.11 m | Authored, 360 cm wide and 460 cm clear. Walks both ways; flooded from x -21000 onward (see Water and swimming). |
| R12 | Atlantis Ruins ↔ Shipwreck | Sealed passage | 14.28 m | Authored, 420 cm wide and 520 cm clear. Walks both ways; fully flooded. |

R01 and R02 meet opposite ends of the Coastal Train Bridge. The bridge interior itself is 577.40 m in the saved route layout; it belongs to the bridge region between those endpoint thresholds. The outer path from the Carnival gate through the bridge interior to the Mansion driveway totals 1028.48 m.

R03–R06 are four route records over one continuous surface spine with 435 generated floor segments, 760 cm nominal width, and 45 cm thickness. The estimated combined spine length is 2990.19 m. The long distance follows the already placed Mansion, Prison, Docks East, and Hospital endpoints; it was not inferred from the illustration's scale. Each graph edge uses its own pair of endpoint records even though the surface is continuous.

R07 and R08 split the existing Carnival-to-Hospital road at the two Slums street interfaces. The estimates use the saved sampled route in Industrial_Hospital_Route_Layout.json and add the authored approach to the Hospital door. The sampled route's current total is 1594.17 m, while the older Industrial Hospital note says 1536 m; neither figure is a new player-timed result.

## Endpoint register and orientation

The full two-sided register is in Connection_Endpoints.json. It records owning package, world position, floor elevation, approximate route-facing yaw, nominal width/height, source report, and status for all R01–R12 endpoints. R01/R02 bridge thresholds are split from the saved mansion route samples; R03 begins at the measured Mansion driveway endpoint. Lower-route anchors follow the authored stair and tunnel geometry.

The mansion driveway anchor is (-69105.978, -84621.550, 598) cm. Docks North, Prison, and Docks East meet the spine at (-55000, -55000, 600), (-30000, -25000, 600), and (70000, 15000, 600) cm. The Hospital endpoint is the existing entry at (95849.499, 129003.284, 642.781) cm.

R10 descends from the Prison service approach at (-27000, -19000, 600) cm to the Sewers entry at (-27000, -12500, -1800) cm. The 120-step stair covers 65 m horizontally and drops 24 m. The Sewer-to-Atlantis and Atlantis-to-Shipwreck connections are separate tunnel passages; no new surface shortcut joins those areas.

## Geometry correction

The Prison source showcase contained two oversized tilted Plane meshes that obstructed the Lab approach and Prison gate. Their collision is now NoCollision in the authored Prison level while their visual backdrops remain. The original vendor pack is unchanged. The Mansion-side outer spine now starts at the measured end of the existing driveway rather than the Mansion center.

## Current verification limit

The main world and authored sublevels were saved. Static route generation and endpoint records do not prove walkability. The actual player route runner loaded the gameplay pawn but stopped after one position sample, so none of R03–R12 is marked traversed. Runtime, loading/unloading, return travel, water sealing, collision, and performance checks remain pending; details are in VALIDATION.md.

## Rotation and Lab B alignment correction (2026-09-30)

`connect_world_expansion.py` built the sublevel rotation as `unreal.Rotator(0.0, yaw, 0.0)`. Unreal Python's positional order is (roll, pitch, yaw), so the Prison (-45), Lab A (-57) and Lab B (123) were **pitched** instead of turned. Their floors were tilted (about 0.54-0.71 walkable normal), Lab B was nearly upside down, and none of their interiors were reachable. The three streaming transforms in the root map are now pure yaw at the same translations (`Scripts/fix_expansion_level_rotation.py`, backup in `Saved/WorldExpansion/LevelRotationFix_20260930`). The connect script now uses keyword arguments.

Upright, Lab B overlapped Lab A, because the authored 180-degree turn folded it back over Lab A. Both rooms share one layout. Lab A's west opening (its removed `SM_MWall03-700x350-8`, local (-1423, 400)) is now met by Lab B's open front (its removed gate, local (1425, 400)). Lab B keeps Lab A's yaw at Lab A-local (-2848, 0) (`Scripts/fix_lab_b_alignment.py`); `author_world_expansion_regions.py` reproduces the same placement.

The west opening still had a lab capsule (`BP_LabCapsule11_1`) standing in it. Lab A's raised platform also sits 50 cm above Lab B's corridor, beyond a 45 cm character step. The capsule prop was removed, and Lab A's own two-step group was mirrored onto the opening (`Scripts/fix_lab_a_west_opening.py`, Lab A backup in `Saved/WorldExpansion/LabAWestOpeningFix_20260930`).

Lab A's `BP_MGate01` opens automatically on approach (PIE: `Saved/CampaignAcceptance/LabGateWalk3_20260930`). In PIE the production character walked from the R09 Lab A entry to the Lab A controls, the Lab B gallery and the Lab B relay, and back. It also walked from the Prison junction to the main-tower base and back (`StationWalkPIE*`/`StationWalkPIEReturn*` and `StationWalkPIEPrisonDesk*` under `Saved/CampaignAcceptance`). This is scripted movement input, not physical controller play, and R03-R08/R10-R12 traversal remains unverified here.

Known remaining defects:

- The Prison main-tower Gothic paintings hang about 6 m up their panels, and their canvases are not visible from reachable ground. Attempts to lower and turn them were reverted.
- Tower paintings D-G sit inside tower floors.
- One spruce foliage instance (#3868 in the Day, Night and NightSnow lighting levels) grows up through Lab A's main room. The available foliage Python API cannot remove a single instance safely.
- Other scripts use the same positional `Rotator(0, yaw, 0)` pattern (stunt-track pieces, boats, foyer note) and may have pitched their objects.

## Route network repairs and verification (2026-10-01)

With the Prison upright, every connection was walked again with the production character in PIE (`playtest_world_expansion_walk_routes.py`, 4x simulation time, crowd excluded from the unsaved test world). Four defects were found and repaired, with backups under `Saved/WorldExpansion/<fix folder>`:

1. **Spine rock.** The Prison showcase rock `SM_Rocks_05` (63 x 29 m) lay across the outer spine; it was removed. The Prison's 5 km x 200 m collision ground strip (`Plane2`, z 580) was trimmed to the Prison footprint plus 50 m (`PrisonRouteBlockers_20261001`).
2. **Prison gate.** The spine's Prison junction control point `(-30000,-25000)` is the outer gate wall's solid end column. The walkable passage is the 2.9 m gap between `SM_WallEntry` and `SM_WallEntryInt` at `(-30158,-24842)`, which the R09 lab branch and the R10 service walk already use. The route runner now steers the spine through that gap. The road slab already covers it, but nothing in the world yet guides a player into it.
3. **Mansion junction.** The spine's first segments overlay the end of the R02 trail 44-99 cm above flat ground, blocking the bridge-to-mansion walk. This had likely been broken since the expansion was added. Segments 0-3 now sit flush on the ground and segments 4-6 form a 7-degree ramp to the unchanged causeway (`SpineJunctionFix_20261001`).
4. **Hospital road.** The spine's last 28 slabs hovered 15-95 cm over the descending hospital road, obstructing it; the motorcycle wedged against them. Fifteen exact duplicates were removed; 1155-1165 now lie flush on the sampled road surface, and 1145-1154 descend about 0.8 degrees to meet them (`SpineJunctionFix_20261001`, `SpineHospitalRoadMerge_20261001`).

Campaign station props that stood on route surfaces were re-sited (see `Docs/CAMPAIGN_AND_INVENTORY.md`). The slums workshop desk had blocked the R07 motorcycle route.

Current results:

| Route | Walk | Motorcycle | Evidence |
| --- | --- | --- | --- |
| R01/R02 Carnival - bridge - Mansion | Pass | Pass | `Saved/MansionConnection/Route_Playtest.json` (after prop re-site) |
| R03-R06 outer spine, Mansion - Hospital, 2.99 km | Pass both ways | Pass both ways | `OuterSpine_After_PropResite_20261001`, `Saved/IndustrialHospital/OuterSpine_Motorcycle_AfterCorner_20261001.json` |
| R07/R08 Carnival - Slums - Hospital road | Pass both ways | Pass both ways | `Saved/IndustrialHospital/Route_Playtest_After_PropResite_20261001.json` |
| R09 Prison - Lab | Pass both ways | n/a | `AfterPrisonBlockers_Walk_20261001` |
| R10 Prison - Sewers (walk + 120-step stair) | Pass both ways | n/a | same |
| R11 Sewers - Atlantis, R12 Atlantis - Shipwreck | Pass both ways | n/a | same |

5. **Spine hairpin.** The spine's authored controls 4-6 (`(-54000,-84000)` -> `(-53000,-84000)` -> `(-54000,-70000)`) made the Catmull curve overshoot into a 15 m lobe with a 141-degree hairpin. Motorcycles could not turn it and caught on its overlapping slab seams. Lobe slabs 473/474 were replaced by one flat 7.6 m corner slab at z 1423 (`SpineHairpinFix_20261001`). Both route runners now drop such overshoot lobes from their paths.

6. **North Dock boat ramp.** `Boat_NorthDock_Inflatable_BoardingDeck_0` was centred so its top end stood 37 cm above the pier, with a slanted end face; the walk to the boat stalled there on every run. Its lower end is kept, and it is shortened from the top so its upper surface meets the pier flush at z 635 and y -55000 (`WaterVehicleAcceptance/RampLipFix_20261001`). Both North Dock lifecycle tests now pass (boat and hovercraft: walk, board, drive out, return, unload, walk back).

**Return to path.** A new pause-menu item moves the player to the nearest of 285 route anchors (`TargetPoint`, tag `CarnivalRouteAnchor`, connectors level) that has a clear standing capsule. It is refused while riding, mounted, in an activity or traversing. Anchors come from positions the production character occupied in today's passing walks, verified station stands and Carnival queue points, each rechecked for floor and capsule (`RouteAnchors_20261001`). It covers walkable pits, which ordinary recovery cannot: their floor keeps refreshing the safe point. Native tests cover pit escape, skipping an occupied anchor, and menu wrap and confirmation (40/40 pass). In PIE it returned the player to grounded walking from nine awkward spots across the world (`ReturnToPathPIE_20261001`). Areas without nearby anchors, such as the Carnival midway interior, fall back to the nearest anchor in range.

The foyer clue note's 14-degree pitch is fixed (yaw 14, flat), and its placement script uses keyword rotators.

These runs use scripted movement input, not a physical controller. Boat and hovercraft travel beyond the North Dock lanes, rendering at normal time, and crowd-active play are not covered by this table. The foyer clue note (`Mission_Foyer_Eli_Physical_Note`) still carries a 14-degree pitch from a positional Rotator; no other affected object was found.

## Region interior reachability audit (2026-10-01)

`Scripts/audit_region_reachability.py` maps every standing-clear walkable floor layer in a region, including upper storeys. It links neighbouring cells with character-realistic directed moves: steps of at most 45 cm with body clearance and floor continuity, and drops of at most 4 m. From a route anchor, it reports traps (reachable cells with no way back), unreachable floor, and whether every route anchor and station stand in the region is reachable and returnable. Use 50 cm cells wherever stairs or narrow doorways matter; a 1 m grid cannot follow hospital stairs. The lab gate and vendor `BP_Door` doors count as passable: since 2026-10-01 the context interact opens and closes every vendor door (see below). Reports are in `Saved/WorldExpansion/Reachability/`.

| Region | Result |
| --- | --- |
| Mansion | All floors and rooms behind openable doors are reachable and returnable; no traps. Only roofs and the exterior lawn below the terrace are unreachable. |
| Labs A/B | All floors reachable and returnable; no traps. |
| Prison | All anchors and the archive desk are reachable and returnable; no traps. Some sealed building floors and rooftops are unreachable. |
| Slums | All anchors and the workshop desk are reachable and returnable. Six tiny terrain dips (1-9 m2) are one-way; Return to path covers them. |
| Hospital (all floors) | **Opened and fixed.** The stairwell `BlockingVolume`s and 15 debris barricades were removed (`HospitalUpperFloorsOpened_20261001`), so all storeys up to z 1543 are reachable. Holes in the upper floors then dropped players into three closed ground-floor rooms and onto wall tops. Five doorway-blocking props (a corpse, bench, bookshelf, treatment table) were slid aside (`HospitalDoorwayBlockers_20261001`). Six invisible slabs (`Hospital_HoleGuard_*`, block all but the camera) now cover the holes that led into spaces with no exit (`HospitalHoleGuards_20261001`). The 50 cm audit: 17,997 cells reachable, all returnable, no traps (`hospital_fine_guarded2_20261001`). |
| Sewers, Atlantis, Shipwreck | R10-R12 walk both ways in PIE. Grid gaps at sloped tunnel floors are audit artefacts. Sewer side sections (`Cube4` floors) beyond closed doors are unreachable. Atlantis and the Shipwreck are now flooded (see Water and swimming). The Shipwreck level references the vendor `UnderwaterShip` sublevels (`Ship`, `SetDressing_Interior`, `SetDressing_Exterior`), but they are not loaded in the composed world, so the wreck shows only its platforms. |
| North Docks | **Fixed.** The spine crossed the docks as a slab 55-110 cm above the decks, so stepping down was one-way. Spine slabs are now flush on the Sandy Arrival and the piers, with transitions of at most 6 degrees. All decks are reachable and returnable. The End Platform is now joined to the Bent Quay by `NorthDock_EndPlatform_Link`, a 4 m deck graded from 635 to 645 (`DockPieceLinks_20261001`). The river under the piers is swimmable; a swimmer climbs out onto the boarding float and walks up the boat ramp to the pier (`RoomExitsClimbOut_20261001`). |
| East Docks | **Fixed.** Quay Approach (580) and Through Walk (625) were raised to 640 to meet the Main Quay (645), and the spine is flush across the decks. No traps. Each loading finger is now joined to the Main Quay by a 4 m deck graded from 645 to 660 (`EastDock_Finger_Link_*`). Every deck is reachable and returnable (`docks_east_linked_20261001`). The East Dock stands on dry ground, so there is no water there. |

The dock levelling uses a continuous profile along the spine (`fix_dock_spine_profile.py`; backups in `DockSpineLevels_20261001` and `DockSpineProfile_20261001`). The outer spine walking and motorcycle runs and both North Dock water-vehicle lifecycles pass after it.

## Vendor doors (2026-10-01)

The 65 vendor `BP_Door*` actors (hospital and mansion) used to stay in their authored pose. `UCarnivalDoorSubsystem` now makes them usable. Context interact near a door swings its leaves 90 degrees away from the player, or closes an open door, over 0.6 s; the HUD shows "Open door" or "Close door". Leaves are the plate meshes (`*Door_Plate*`, `SM_Door02_D/E`), and the closed pose is the frame's yaw. Static leaves are made movable when first used. The music-room door stays under its mission interaction. Native test `Carnival.World.VendorDoors`. In PIE, every probed non-mission door opened, and the character walked through every probed doorway except the hospital double door `BP_Door_02a2`, which stops it about 36 cm past the frame (`VendorDoorsInteractPIE_20261001`, `WaterPIE_v2_20261001`).

## Water and swimming (2026-10-01)

Swimming water is `ACarnivalWaterVolume`, a box physics volume sized by `WaterExtent` whose box is built into the brush collision. Engine swimming, surface floating and leaving the water all behave as normal UE water. All volumes are in the always-loaded connectors level.

| Water | Volumes | Notes |
| --- | --- | --- |
| River (incl. North Dock) | 59 `Water_River_*` boxes, surface -240 | The `WaterBodyRiver` is a 1 km wide sheet at z -240; its water shows wherever the landscape dips below that level. 50 m cells inside the band, from 2 m below the local riverbed up to the surface, merged along X (`WaterVolumesRiver_v2_20261001`). The editor-only far-terrain mesh `SM_Landscape_Far_01a` covers the docks in the editor and must be ignored by editor traces. |
| Dry override | `Water_DryOverride_SewersAndStair` (not water, priority 20) | Keeps the prison stair, Sewers and sewer tunnel dry even where the river band lies above them. |
| Atlantis and Shipwreck | `Water_Flooded_AtlantisShipwreck` (priority 30), x -21000..-4000, z -2500..-500 | Flooded from partway along the sewer tunnel (a translucent waterline sheet, `SewerToAtlantis_Waterline`, marks the start) through both interiors. A solid lid at -500 keeps swimmers in the water. |

Character behaviour (`ACarnivalPlayerCharacter`):
- **Controls:** hold jump to swim up and hold crouch to dive. Fully under water, forward follows the camera pitch beyond 20 degrees.
- **Floating and sinking:** within 1.5 m of the surface an idle swimmer floats with the head out. Deeper, they sink slowly onto the bottom and walk there at 260 cm/s; jump lifts off again.
- **Getting out:** swimming at the surface into a walkable ledge up to 1.5 m above the water climbs out onto it.
- **Animations:** the four FreeAnimationLibrary swim loops (idle, forward, left, right), retargeted to the player skeleton in `/Game/Carnival/Character/Animations/Swim`, play on `DefaultSlot` while swimming. There are no underwater-stroke, dive or climb-out animations in the project.
- **Underwater look:** with the camera inside water, the camera post-process applies `M_CarnivalUnderwaterPP` (depth fog, with everything above the surface fully fogged) plus a blue-green grade.
- **Recovery:** swimming in authored water no longer raises the "Recovery available" prompt; Return to path still works.

- **Flooded passages:** `UCarnivalCharacterMovementComponent` keeps a walking character on the floor when it walks into water deeper than its head, such as the flooded sewer tunnel, instead of the engine forcing swimming. Stepping off a ledge on the bottom sinks as a slow fall (35% gravity) unless a swim input is held.

Native test `Carnival.Player.SwimAndSeabed`, which covers dive, seabed walk, rise, float, settle, climb-out and walking into a flooded corridor. Rendered PIE evidence: `WaterPIE_v2_20261001`. With the water in place, the route walks still pass both ways: the full set in `Walk_Route_Playtest_AfterWater_20261001`, with R11 and R12 re-run after the fixes (`Walk_Route_Playtest_Flooded_20261001`, `Walk_Route_Playtest_Flooded_R11_20261001`). The waterline sheet first kept its `BlockAll` collision profile and stopped walkers; it now uses `NoCollision`.
