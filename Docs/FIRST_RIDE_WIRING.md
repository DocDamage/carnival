# First Ride Wiring — Swing (Creepwood, in LV_Carnival)

> **Automated**: `Scripts/wire_ride.py` already derives `BP_Swing_Carnival` and adds the
> controller/motion/queue components plus 34 seat components (one per chair). The
> remaining steps below (motion source, queue markers, timeline hooks, MetaHuman) are
> manual/editor work. The derived Blueprint lives at `/Game/Carnival/Rides/BP_Swing_Carnival`.

The Ferris Wheel and Carousel are **not** placed in the `LV_Carnival` showcase map (they
live in the `Lv_LightingDay/Night/NightSnow` maps), so the recommended first ride is the
**Swing** (`BP_Swing_Ride_01a`), with the **Pirate Ship** (`BP_PirateShip_Ride_01a`) as an
equally valid alternative.

## Swing — discovered internals (from `dump_ride_components.py`)

- Motion: `RotatingMovement_Anchor` + `RotatingMovement_Sphere` (two `RotatingMovementComponent`s).
- Moving assembly: `MainAnchor` (SceneComponent, MOVABLE) and `Swings` (SceneComponent,
  parented under `Tent`).
- Seats: ~17 suspended chairs `SM_Swing_Chair_10..26`, each parented to a chain
  (`SM_Swing_Chair_ChainNN`).
- Control: `StartRide` / `StopRide` / `TurnOnRide` / `TurnOffRide` (from `BP_Rides_Parent`),
  `E_RideState` = `Starting | Started | Stopping | Stopped`.

## General principle (applies to every Creepwood ride)

The ride motion is either `RotatingMovementComponent`-driven or Timeline-driven. Point
`UCarnivalRideMotionComponent::SetMotionSource` at the actual **moving SceneComponent**:

| Ride | Motion source for `SetMotionSource` |
|---|---|
| Swing | `MainAnchor` (or `Swings`) |
| Pirate Ship | `SM_Mainboat_PirateRide` |
| Teapot | `SM_Teapot_Ride_Platform4` |
| Ferris Wheel | rotating wheel / `SM_Cabin_01a` gondolas |
| Balloon Tower | `RotatingMovement_SeatN` (per seat) |
| Clown Ride | `Anchor_CenterPiece` |
| Carousel | `SharedRoot` / `Body_MainAnchor` |

## Swing wiring steps (Unreal Editor)

1. **Derive a child Blueprint** from the in-map Swing instance (class
   `BP_Swing_Ride_01a_C`) — never modify the purchased Blueprint destructively.
2. Add to the derived Blueprint:
   - `CarnivalRideControllerComponent` (`RideId = "Swing"`, `ExitTransform` beside the gate).
   - `CarnivalRideMotionComponent` — in `BeginPlay`, call
     `SetMotionSource` with the `MainAnchor` component.
   - `CarnivalRideQueueComponent` (`RideId = "Swing"`).
3. **Seats**: add one `CarnivalRideSeatComponent` per chair, parented to
   `SM_Swing_ChairNN` so seats inherit rotation + chain swing. Set:
   - unique `SeatId` (e.g. `Chair10`, `Chair11`, …),
   - `RestraintType = LapBar` (chairs have a front bar),
   - `PassengerOffset` (pelvis aligned to the chair seat),
   - `LeftHandTarget` / `RightHandTarget` on the lap bar,
   - foot targets on the foot rest.
4. **Queue markers**: `CarnivalQueuePoint` actors along the physical queue, `RideId = "Swing"`,
   `QueueIndex` from `0` (gate) outward.
5. **Hook vendor timeline**: around the existing `StartRide` / `StopRide` calls add
   `SetRidePhase(Loading)` → `SetRidePhase(Locked)` → `SetRidePhase(Running)` →
   `SetRidePhase(Unloading)` + `UnboardAllPassengers()` → `SetRidePhase(Loading)`.
6. **Board flow**: `QueueComponent->EnqueueGuest(Guest)` → `PopNextGuest()` →
   `ControllerComponent->BoardPassenger(Guest)`.

## Pirate Ship alternative

- Motion source: `SM_Mainboat_PirateRide` (Timeline-driven pendulum via `PirateShipAnimation`).
- Seats: add `CarnivalRideSeatComponent`s parented to the boat, one per bench position,
  `RestraintType = LapBar`. The boat's Timeline already swings it; the motion component
  samples `SM_Mainboat_PirateRide` to derive telemetry.

## Validation checklist

- [ ] passenger stays seated for a full rotation (+ chain swing)
- [ ] seat follows the chair/boat with no drift
- [ ] hands reach the lap bar / restraint
- [ ] telemetry fires during motion (speed/lateral/angular)
- [ ] reactions change with intensity and personality
- [ ] unload position is clear of the moving assembly
- [ ] repeated cycles don't leak occupancy
