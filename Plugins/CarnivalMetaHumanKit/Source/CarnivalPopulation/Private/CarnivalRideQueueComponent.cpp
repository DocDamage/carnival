#include "CarnivalRideQueueComponent.h"
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
    if (!IsValid(Guest))
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
    for (int32 GuestIndex = 0; GuestIndex < WaitingGuests.Num(); ++GuestIndex)
    {
        if (WaitingGuests[GuestIndex].Get() == Guest)
        {
            Index = GuestIndex;
            break;
        }
    }

    if (!QueuePoints.IsValidIndex(Index) || !IsValid(QueuePoints[Index]))
    {
        return FTransform::Identity;
    }

    return QueuePoints[Index]->GetActorTransform();
}

int32 UCarnivalRideQueueComponent::GetQueueLength() const
{
    return WaitingGuests.Num();
}

int32 UCarnivalRideQueueComponent::GetQueueCapacity() const
{
    return QueuePoints.Num();
}

bool UCarnivalRideQueueComponent::HasOpenSlot() const
{
    return WaitingGuests.Num() < QueuePoints.Num();
}
