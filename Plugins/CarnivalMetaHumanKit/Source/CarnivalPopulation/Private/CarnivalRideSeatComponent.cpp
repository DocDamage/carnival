#include "CarnivalRideSeatComponent.h"

UCarnivalRideSeatComponent::UCarnivalRideSeatComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool UCarnivalRideSeatComponent::IsOccupied() const
{
    return IsValid(Occupant);
}

AActor* UCarnivalRideSeatComponent::GetOccupant() const
{
    return Occupant;
}

static FTransform CarnivalCombine(const USceneComponent* Component, const FTransform& Local)
{
    return Local * Component->GetComponentTransform();
}

FTransform UCarnivalRideSeatComponent::GetPassengerWorldTransform() const
{
    return CarnivalCombine(this, PassengerOffset);
}

FTransform UCarnivalRideSeatComponent::GetLeftHandWorldTransform() const
{
    return CarnivalCombine(this, LeftHandTarget);
}

FTransform UCarnivalRideSeatComponent::GetRightHandWorldTransform() const
{
    return CarnivalCombine(this, RightHandTarget);
}

FTransform UCarnivalRideSeatComponent::GetLeftFootWorldTransform() const
{
    return CarnivalCombine(this, LeftFootTarget);
}

FTransform UCarnivalRideSeatComponent::GetRightFootWorldTransform() const
{
    return CarnivalCombine(this, RightFootTarget);
}
