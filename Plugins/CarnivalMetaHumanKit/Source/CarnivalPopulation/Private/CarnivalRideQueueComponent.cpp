#include "CarnivalRideQueueComponent.h"
#include "Engine/World.h"
#include "CarnivalQueuePoint.h"
#include "Kismet/GameplayStatics.h"

UCarnivalRideQueueComponent::UCarnivalRideQueueComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UCarnivalRideQueueComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bDiscoverQueuePointsAtBeginPlay)
    {
        DiscoverQueuePoints();
    }
}

void UCarnivalRideQueueComponent::DiscoverQueuePoints()
{
    QueuePoints.Reset();
    if (!IsValid(GetWorld()))
    {
        return;
    }

    TArray<AActor*> Found;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), ACarnivalQueuePoint::StaticClass(), Found);
    for (AActor* Actor : Found)
    {
        ACarnivalQueuePoint* Point = Cast<ACarnivalQueuePoint>(Actor);
        if (IsValid(Point) && (RideId.IsNone() || Point->RideId == RideId))
        {
            QueuePoints.Add(Point);
        }
    }

    // UE 5.8: TArray<TObjectPtr<T>>::Sort dereferences elements before invoking the
    // predicate, so the comparator receives const ACarnivalQueuePoint& (not the TObjectPtr).
    // Elements are validated for null before being added to QueuePoints above.
    QueuePoints.Sort([](const ACarnivalQueuePoint& A, const ACarnivalQueuePoint& B)
    {
        return A.QueueIndex < B.QueueIndex;
    });
}

bool UCarnivalRideQueueComponent::EnqueueGuest(AActor* Guest)
{
    WaitingGuests.RemoveAll([](const TObjectPtr<AActor>& Existing) { return !IsValid(Existing); });
    if (!IsValid(Guest) || !HasOpenSlot())
    {
        return false;
    }

    for (AActor* Existing : WaitingGuests)
    {
        if (Existing == Guest)
        {
            return false;
        }
    }

    WaitingGuests.Add(Guest);
    OnGuestEnqueued.Broadcast(Guest);
    return true;
}

bool UCarnivalRideQueueComponent::RemoveGuest(AActor* Guest)
{
    if (!Guest)
    {
        return false;
    }

    for (int32 Index = 0; Index < WaitingGuests.Num(); ++Index)
    {
        if (WaitingGuests[Index].Get() == Guest)
        {
            WaitingGuests.RemoveAt(Index);
            OnGuestDequeued.Broadcast(Guest);
            return true;
        }
    }
    return false;
}

AActor* UCarnivalRideQueueComponent::PopNextGuest()
{
    while (WaitingGuests.Num() > 0)
    {
        AActor* Guest = WaitingGuests[0].Get();
        WaitingGuests.RemoveAt(0);
        if (IsValid(Guest))
        {
            OnGuestDequeued.Broadcast(Guest);
            return Guest;
        }
    }
    return nullptr;
}

FTransform UCarnivalRideQueueComponent::GetGuestQueueTarget(AActor* Guest) const
{
    if (!IsValid(Guest))
    {
        return FTransform::Identity;
    }

    int32 Index = INDEX_NONE;
    int32 LiveIndex = 0;
    for (const auto& Waiting : WaitingGuests)
    {
        if (!IsValid(Waiting)) continue;
        if (Waiting.Get() == Guest)
        {
            Index = LiveIndex;
            break;
        }
        ++LiveIndex;
    }

    if (Index == INDEX_NONE) return FTransform::Identity;
    LiveIndex = 0;
    for (const auto& Point : QueuePoints)
    {
        if (!IsValid(Point)) continue;
        if (LiveIndex++ == Index) return Point->GetActorTransform();
    }
    return FTransform::Identity;
}

int32 UCarnivalRideQueueComponent::GetQueueLength() const
{
    int32 Count = 0;
    for (const auto& Guest : WaitingGuests) if (IsValid(Guest)) ++Count;
    return Count;
}

int32 UCarnivalRideQueueComponent::GetQueueCapacity() const
{
    int32 Count = 0;
    for (const auto& Point : QueuePoints) if (IsValid(Point)) ++Count;
    return Count;
}

bool UCarnivalRideQueueComponent::HasOpenSlot() const
{
    return GetQueueLength() < GetQueueCapacity();
}
