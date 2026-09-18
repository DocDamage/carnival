#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalTypes.h"
#include "CarnivalRideActor.generated.h"

class UCarnivalRideMotionComponent;
class UCarnivalRidePassengerComponent;
class UCarnivalRideSeatComponent;
class USceneComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FCarnivalRidePhaseChangedSignature, ECarnivalRidePhase, OldPhase, ECarnivalRidePhase, NewPhase);

UCLASS(Blueprintable)
class CARNIVALPOPULATION_API ACarnivalRideActor : public AActor
{
    GENERATED_BODY()

public:
    ACarnivalRideActor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Carnival|Ride")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Carnival|Ride")
    TObjectPtr<UCarnivalRideMotionComponent> MotionTelemetry;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride")
    FName RideId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride")
    FTransform ExitTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category="Carnival|Ride")
    ECarnivalRidePhase RidePhase = ECarnivalRidePhase::Closed;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Ride")
    FCarnivalRidePhaseChangedSignature OnRidePhaseChanged;

    UFUNCTION(BlueprintCallable, Category="Carnival|Ride")
    void RefreshSeats();

    UFUNCTION(BlueprintPure, Category="Carnival|Ride")
    TArray<UCarnivalRideSeatComponent*> GetSeats() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Ride")
    UCarnivalRideSeatComponent* FindAvailableSeat() const;

    UFUNCTION(BlueprintCallable, Category="Carnival|Ride")
    bool BoardPassenger(AActor* Passenger);

    UFUNCTION(BlueprintCallable, Category="Carnival|Ride")
    void UnboardAllPassengers();

    UFUNCTION(BlueprintCallable, Category="Carnival|Ride")
    void SetRidePhase(ECarnivalRidePhase NewPhase);

    UFUNCTION(BlueprintCallable, Category="Carnival|Ride")
    void PushTelemetryToPassengers(const FCarnivalRideTelemetry& Telemetry);

protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(Transient)
    TArray<TObjectPtr<UCarnivalRideSeatComponent>> Seats;
};
