# Ferris Wheel — Ride Wiring Guide (Creepwood)

> NOTE: the Ferris Wheel (and Carousel) are **not** placed in `LV_Carnival`. They live in
> the `Lv_LightingDay`, `Lv_LightingNight` and `Lv_LightingNightSnow` maps. To wire the
> Ferris Wheel, open one of those maps (or migrate a Ferris Wheel instance into
> `LV_Carnival`). For a ride already present in `LV_Carnival`, see `FIRST_RIDE_WIRING.md`.

Target ride: `BP_FerrisWheel_Ride_01a` (base) or the in-map material variant
`BP_FerrisWheel_Ride_01a_<Variant>` under `Environment/Blueprint/Ride/Instance/`.

## Discovered internals (from the Blueprint binary string table)

- Parent class: `BP_Rides_Parent` (shared ride control/timeline logic).
- Motion source: `RotatingMovementComponent` (`RotatingMovement`).
- Cabins: `Local_leftSphereCabins` / `Local_rightSphereCabins` / `Local_sortedCombinedCabins`,
  `Local_currentCabin`, `Local_currentCabinSM`, `Local_currentMasterComponent`.
- Cabin swing physics: `PhysicsConstraintComponent` + `PhysicalAnimationComponent`.
- Ride control functions: `StartRide`, `StopRide`, `TurnOnRide`, `TurnOffRide`.
- Ride phase enum: `E_RideState` = `Starting | Started | Stopping | Stopped`.

## Goal

Preserve the vendor ride animation/timeline. Add CarnivalKit components to a **derived**
child Blueprint so the purchased assets are never modified destructively.

## Step-by-step (Unreal Editor)

1. **Derive a Blueprint**
   - Right-click the in-map Ferris Wheel instance → "Create Child Blueprint Class", or
     create a new Blueprint whose parent is `BP_FerrisWheel_Ride_01a` (or its Instance variant).
   - Name it `BP_FerrisWheel_Ride_Carnival`.

2. **Add CarnivalKit components** to the derived Blueprint:
   - `CarnivalRideControllerComponent` (set `RideId = "FerrisWheel"`, `ExitTransform` to a
     safe local-space load/unload point beside the gate).
   - `CarnivalRideMotionComponent` (call `SetMotionSource` in `BeginPlay` with the
     rotating wheel/cabin root `RotatingMovement` component — or the root wheel SceneComponent).
   - `CarnivalRideQueueComponent` (set `RideId = "FerrisWheel"`, keep auto-discover on).

3. **Add seats**
   - For each gondola, add a `CarnivalRideSeatComponent` parented to the gondola mesh so it
     inherits the wheel + physics-swing motion.
   - Rotate each seat so +X is the guest forward direction.
   - Set a unique `SeatId` (e.g. `Cabin01_A`, `Cabin01_B`, …).
   - Set `RestraintType` (Ferris gondolas are usually `None` or `SeatBelt`).
   - Tune `PassengerOffset` so the pelvis sits naturally on the bench.
   - Place `LeftHandTarget` / `RightHandTarget` on the handrail/bar; foot targets on the floor.

4. **Queue markers**
   - Place `CarnivalQueuePoint` actors along the physical Ferris queue with
     `RideId = "FerrisWheel"`, numbered from `0` (gate) outward.

5. **Hook the vendor timeline** (in the derived Blueprint event graph, around the existing
   `StartRide` / `StopRide` / `TurnOnRide` / `TurnOffRide` calls):
   - before boarding → `SetRidePhase(Loading)`
   - after boarding batch / doors close → `SetRidePhase(Locked)`
   - when `StartRide`/`TurnOnRide` runs → `SetRidePhase(Running)`
   - when `StopRide`/`TurnOffRide` runs → `SetRidePhase(Unloading)` + `UnboardAllPassengers()`
   - after unload → `SetRidePhase(Loading)`

6. **Board flow** (from queue/AI):
   - `QueueComponent->EnqueueGuest(Guest)`
   - `QueueComponent->PopNextGuest()` → `ControllerComponent->BoardPassenger(Guest)`

## Validation checklist

- [ ] passenger stays seated for a full wheel revolution + cabin swing
- [ ] seat follows the gondola (no drift)
- [ ] hands reach handrail targets
- [ ] reaction events fire during motion (telemetry from `SetMotionSource` component)
- [ ] unload position is clear of the moving wheel
- [ ] repeated cycles do not strand passengers or leak occupancy
