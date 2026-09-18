# MetaHuman Crowd / Mass setup — UE 5.8

MetaHuman Crowd remains experimental in UE 5.8, so CarnivalKit keeps boarding and ride gameplay independent from its C++ API.

## Plugins

Enable:

- MetaHuman Crowd
- Mass AI
- Mass Crowd
- StateTree
- ZoneGraph
- Smart Objects

The installer attempts to enable these in the `.uproject`.

## Crowd asset pipeline

1. Create/import adult MetaHumans, compatible grooms and clothing.
2. Create a MetaHuman Collection.
3. Assign the Crowd Pipeline.
4. Build the Collection.
5. Create many MetaHuman Instances with different heads/hair/clothing/material variations.
6. Create a Mass Entity Config.
7. Add MetaHuman Crowd visualization.
8. Add `CrowdMember` for crowd navigation.
9. Add a StateTree trait if you want behavior states.
10. Place the MetaHuman Mass Spawner in the carnival.
11. Add a Nav Mesh Bounds Volume for the walkable midway.
12. Build ZoneGraph paths where you want deliberate pedestrian flow.

## Suggested population target for initial testing

Start with:

```text
Visible crowd target: 75–100
High-fidelity/full actors near player: ~8–10
Remaining guests: crowd representations / lower LOD
```

Do not tune final density until the full carnival lighting, rides and post-processing are active.

## Guest Blueprint bridge

On the high-fidelity actor Blueprint used by the MetaHuman crowd actor representation:

1. Add `CarnivalRidePassengerComponent`.
2. Implement `CarnivalPassengerInterface`.
3. In `CarnivalRideBoarded`:
   - disable locomotion / player-style movement
   - set `bIsRiding = true` in your animation layer
   - store the seat/restraint type if needed
4. In `CarnivalRideReactionChanged`:
   - write Reaction + Strength to the Anim Blueprint
   - drive body additive animation and facial response
5. In `CarnivalRideUnboarded`:
   - clear riding state
   - restore locomotion

## Promoting a crowd guest to a rider

CarnivalKit deliberately leaves Mass-to-Actor promotion as a Blueprint/integration boundary because the experimental crowd API may change.

Your StateTree/interaction flow should be:

```text
Wander
 -> choose ride
 -> queue
 -> request high-fidelity actor representation
 -> BoardPassenger
 -> ride
 -> Unboard
 -> return guest to crowd behavior
```

This keeps queue/ride logic stable even if Epic changes the MetaHuman Crowd internals.
