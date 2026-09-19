#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalTypes.h"
#include "CarnivalRideControllerComponent.generated.h"

class UCarnivalRideMotionComponent;
class UCarnivalRideSeatComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FCarnivalControllerPhaseChangedSignature, ECarnivalRidePhase, OldPhase, ECarnivalRidePhase, NewPhase);

UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALPOPULATION_API UCarnivalRideControllerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCarnivalRideControllerComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride")
    FName RideId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride")
    FTransform ExitTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category="Carnival|Ride")
    ECarnivalRidePhase RidePhase = ECarnivalRidePhase::Closed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride", meta=(ToolTip="Automatically transition ride phases from motion telemetry (replaces manual StartRide/StopRide hooks)."))
    bool bAutoDetectPhase = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride", meta=(EditCondition="bAutoDetectPhase", ClampMin="0.0", ToolTip="Speed (cm/s) above which the ride is considered Running."))
    float MotionStartSpeed = 40.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride", meta=(EditCondition="bAutoDetectPhase", ClampMin="0.0", ToolTip="Speed (cm/s) below which the ride is considered stopped."))
    float MotionStopSpeed = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Ride", meta=(EditCondition="bAutoDetectPhase", ClampMin="0.0", ToolTip="How long motion must stay below stop speed before unloading."))
    float StopHoldDuration = 1.5f;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Ride")
    FCarnivalControllerPhaseChangedSignature OnRidePhaseChanged;

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
    UFUNCTION()
    void HandleTelemetry(const FCarnivalRideTelemetry& Telemetry);

    UPROPERTY(Transient)
    TArray<TObjectPtr<UCarnivalRideSeatComponent>> Seats;

    float TimeBelowStopThreshold = 0.0f;
};
