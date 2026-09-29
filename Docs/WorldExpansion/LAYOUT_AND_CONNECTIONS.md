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
| Research Lab B | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB | (-42524.989, -5651.722, 600); 123 deg | Secondary research room aligned to Lab A through its door opening. |
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
| R11 | Sewers ↔ Atlantis Ruins | Sealed passage | 82.11 m | Authored, 360 cm wide and 460 cm clear; traversal and water sealing pending. |
| R12 | Atlantis Ruins ↔ Shipwreck | Sealed passage | 14.28 m | Authored, 420 cm wide and 520 cm clear; traversal and water sealing pending. |

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
