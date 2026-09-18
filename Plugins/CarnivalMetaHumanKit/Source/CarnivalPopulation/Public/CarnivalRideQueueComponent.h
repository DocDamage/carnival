#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalRideQueueComponent.generated.h"

class ACarnivalQueuePoint;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarnivalQueueGuestSignature, AActor*, Guest);

UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALPOPULATION_API UCarnivalRideQueueComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCarnivalRideQueueComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Queue")
    FName RideId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Queue")
    bool bDiscoverQueuePointsAtBeginPlay = true;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Queue")
    FCarnivalQueueGuestSignature OnGuestEnqueued;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Queue")
    FCarnivalQueueGuestSignature OnGuestDequeued;

    UFUNCTION(BlueprintCallable, Category="Carnival|Queue")
    void DiscoverQueuePoints();

    UFUNCTION(BlueprintCallable, Category="Carnival|Queue")
    bool EnqueueGuest(AActor* Guest);

    UFUNCTION(BlueprintCallable, Category="Carnival|Queue")
    bool RemoveGuest(AActor* Guest);

    UFUNCTION(BlueprintCallable, Category="Carnival|Queue")
    AActor* PopNextGuest();

    UFUNCTION(BlueprintPure, Category="Carnival|Queue")
    FTransform GetGuestQueueTarget(AActor* Guest) const;

    UFUNCTION(BlueprintPure, Category="Carnival|Queue")
    int32 GetQueueLength() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Queue")
    int32 GetQueueCapacity() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Queue")
    bool HasOpenSlot() const;

protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(Transient)
    TArray<TObjectPtr<ACarnivalQueuePoint>> QueuePoints;

    UPROPERTY(Transient)
    TArray<TObjectPtr<AActor>> WaitingGuests;
};
