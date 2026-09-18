# Creepwood Wonderland wiring

The fastest route is to preserve the vendor ride Blueprints and add CarnivalKit components to them rather than rebuilding the rides.

## Per ride

Open the ride Blueprint and add:

1. `CarnivalRideControllerComponent`
2. `CarnivalRideMotionComponent`
3. `CarnivalRideQueueComponent`
4. One `CarnivalRideSeatComponent` per passenger seat

For each seat:

- parent the seat component under the actual moving gondola/car/bench component
- rotate the seat so +X is the guest's forward direction
- adjust `PassengerOffset` until the pelvis/body is aligned correctly
- place `LeftHandTarget` and `RightHandTarget` on the restraint or handle
- optionally tune foot targets
- choose the restraint type
- give every seat a unique `SeatId`

For `CarnivalRideMotionComponent`, call `SetMotionSource` at BeginPlay with the moving ride component that best represents passenger motion. On a Ferris wheel this can be a gondola or wheel reference; on a pirate ship use the swinging body; on a spinning ride use the rotating platform/car reference.

## Existing ride timeline integration

Do not replace the pack's animation/timeline logic. Add these calls around it:

```text
Before boarding:
    RideController -> SetRidePhase(Loading)

After seats are filled / restraints close:
    RideController -> SetRidePhase(Locked)

When existing ride animation starts:
    RideController -> SetRidePhase(Running)

When animation finishes:
    RideController -> SetRidePhase(Unloading)
    RideController -> UnboardAllPassengers()

After unload:
    RideController -> SetRidePhase(Loading)
```

The motion component automatically broadcasts telemetry during the running phase.

## Boarding

Any full actor with `CarnivalRidePassengerComponent` can be passed to:

```text
RideController -> BoardPassenger(GuestActor)
```

The controller takes the first open seat.

## Exit transform

Set the controller's `ExitTransform` to a safe local-space point beside the ride exit. `UnboardAllPassengers` places riders there.

## Ride inventory template

`Examples/CreepwoodRideProfiles.json` lists the Creepwood attractions identified from the store listing. Seat counts are deliberately zero until the actual licensed level is inspected; guessing would create bad setup data.

## Recommended first ride

Wire one mechanically simple ride first, such as the Ferris Wheel, Carousel, Swing, or Pirate Ship. Validate:

- actor stays seated for the entire motion
- seat follows the moving component
- hands reach sensible targets
- reaction events fire
- unload position is safe

Then copy the pattern to the other rides.


## Queue integration

Place `CarnivalQueuePoint` actors along the physical queue, give them the same `RideId`, and number them from `0` at the boarding gate outward. The queue component discovers and sorts them at BeginPlay.

Use:

```text
EnqueueGuest(Guest)
GetGuestQueueTarget(Guest)
PopNextGuest() -> BoardPassenger(Guest)
```

StateTree or AI movement remains responsible for moving the guest to the returned target.

## Layout helpers

`CarnivalLayoutLibrary` provides row, grid, radial, and serpentine transform generators. These are useful in Blueprint Construction Scripts for quickly roughing in seat/queue layouts before hand-aligning them to the vendor geometry.
