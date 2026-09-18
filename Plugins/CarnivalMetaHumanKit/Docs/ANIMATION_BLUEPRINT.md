# Ride animation blueprint contract

CarnivalKit produces state and transforms; it does not ship copyrighted or third-party animation assets.

## Variables to expose in the guest Anim Blueprint

```text
bIsRiding : bool
RideReaction : ECarnivalRideReaction
RideReactionStrength : float
RestraintType : ECarnivalRestraintType
LeftHandIK : Transform
RightHandIK : Transform
LeftFootIK : Transform
RightFootIK : Transform
```

## Recommended layers

```text
Base seated pose
 + lean/brace additive
 + reaction additive
 + hand/foot IK
 + head/eye look
 + facial reaction
```

## Reaction mapping

| Reaction | Suggested body behavior |
|---|---|
| Calm | seated idle / look around |
| Grip | brace torso, both hands on restraint |
| LeanLeft | additive left lean |
| LeanRight | additive right lean |
| HandsUp | hands-up pose, disable hand IK temporarily |
| Laugh | light upper-body reaction + face |
| Cheer | larger gesture / head movement |
| Scream | brace or hands-up + strong face |
| Brace | forward/core brace |
| Relief | settle, exhale/laugh after ride |

## Seat IK

Use `CarnivalBlueprintLibrary -> GetSeatIKTarget` with target names:

```text
LeftHand
RightHand
LeftFoot
RightFoot
```

For most rides, hand IK is more important than foot IK.
