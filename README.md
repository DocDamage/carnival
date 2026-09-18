# CarnivalMetaHuman

A living amusement park built on the **Creepwood Wonderland** carnival environment
(Unreal Engine **5.8**), populated with MetaHuman/Mass crowd guests who wander, queue,
board attractions, physically sit, react to ride motion, and return to the crowd.

## Structure

- `Plugins/CarnivalMetaHumanKit/` — reusable C++/Blueprint ride-passenger foundation
  (`CarnivalRidePassengerComponent`, `CarnivalRideSeatComponent`,
  `CarnivalRideControllerComponent`, `CarnivalRideMotionComponent`,
  `CarnivalRideQueueComponent`, queue/activity-zone actors, layout helpers, installer).
- `Source/CarnivalGame/` — minimal C++ game module.
- `Content/Carnival/` — custom content (derived ride Blueprints, e.g. `BP_Swing_Carnival`).
- `Docs/` — integration status and ride-wiring guides.
- `Scripts/` — editor Python automation (level scan, component dump, ride wiring).
- `Config/` — project + ride inventory configuration.

## Important — licensed Creepwood content

The purchased Creepwood content (`Content/Creepwood_Carnival_Meshingun/`) is **not**
committed. Add your own licensed copy from the Epic Games Launcher (VaultCache) into
`Content/Creepwood_Carnival_Meshingun/` before opening the project.

## Build

Unreal Engine 5.8 (Windows). See `Docs/CARNIVAL_INTEGRATION_STATUS.md` for the full
integration status, ride inventory, and next steps.
