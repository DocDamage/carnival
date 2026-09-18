# CarnivalMetaHumanKit — UE 5.8

Drop-in C++/Blueprint foundation for populating an adult carnival with MetaHuman Crowd/Mass characters and seating promoted/full actors on moving rides.

## What is already built

- `UCarnivalRidePassengerComponent`
  - deterministic personality generation
  - board/unboard logic
  - seat attachment
  - ride reaction selection from telemetry
  - Blueprint events for animation/facial logic
- `UCarnivalRideSeatComponent`
  - passenger placement offset
  - left/right hand IK targets
  - left/right foot IK targets
  - restraint type and occupancy
- `UCarnivalRideControllerComponent`
  - designed to be added directly to third-party ride Blueprints such as Creepwood
  - seat discovery
  - boarding/unboarding
  - ride phase management
  - telemetry distribution
- `UCarnivalRideMotionComponent`
  - samples a moving scene component
  - speed, acceleration, vertical/lateral acceleration, angular speed, normalized intensity
- `ICarnivalPassengerInterface`
  - BlueprintNativeEvents for boarded/reaction/unboarded
- `ACarnivalRideActor`
  - optional standalone wrapper for rides you author yourself
- `ACarnivalQueuePoint` + `UCarnivalRideQueueComponent`
  - ordered queue markers, capacity, enqueue/dequeue, per-guest queue targets
- `ACarnivalActivityZone`
  - wander/ride queue/food/game/seating/spectator/exit marker
- `UCarnivalBlueprintLibrary`
  - seat IK access and intensity helper
- `UCarnivalLayoutLibrary`
  - row/grid/radial seat layouts and serpentine queue transform generation
- Unreal Editor Python helpers
  - create content folders
  - scan a loaded Creepwood level for likely ride actors
- PowerShell installer
  - copies plugin to a UE project
  - enables CarnivalPopulation + MetaHuman Crowd/Mass dependencies

## Recommended architecture

MetaHuman Crowd/Mass owns the cheap roaming population. A guest that needs close-up interaction or a ride seat should use a high-fidelity actor representation with `CarnivalRidePassengerComponent`. The ride system itself does not link directly against MetaHuman Crowd, which prevents the gameplay layer from being locked to an experimental API.

## Install

From PowerShell:

```powershell
.\Scripts\Install-CarnivalPopulation.ps1 -ProjectPath "D:\MyGame\MyGame.uproject"
```

Then regenerate project files/build and open the project in Unreal Engine 5.8.

You can also copy the entire folder to:

```text
<MyProject>/Plugins/CarnivalMetaHumanKit/
```

## First editor steps

1. Run `Scripts/prepare_content_folders.py` from Unreal's Python console.
2. Load the Creepwood showcase map.
3. Run `Scripts/scan_creepwood_level.py`.
4. Inspect `Saved/CarnivalKit/CreepwoodRideCandidates.json`.
5. Follow `Docs/CREEPWOOD_WIRING.md` for one ride end-to-end.
6. Follow `Docs/METAHUMAN_CROWD_SETUP.md` for the roaming population.

## Important limitation

This package does not contain the purchased Creepwood content, MetaHuman assets, animations, or `.uasset` Blueprints. Those assets must be wired in your licensed Unreal project. The source is intentionally asset-agnostic so it can be compiled and reused without redistributing third-party content.
