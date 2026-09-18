#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalTypes.h"
#include "CarnivalRidePassengerComponent.generated.h"

class UCarnivalRideSeatComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FCarnivalReactionChangedSignature, ECarnivalRideReaction, Reaction, float, Strength, FCarnivalRideTelemetry, Telemetry);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FCarnivalBoardedSignature, AActor*, RideActor, UCarnivalRideSeatComponent*, Seat);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarnivalUnboardedSignature, AActor*, RideActor);

UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALPOPULATION_API UCarnivalRidePassengerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCarnivalRidePassengerComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger")
    FCarnivalGuestPersonality Personality;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger")
    bool bAutoGeneratePersonality = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger")
    int32 PersonalitySeed = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger")
    bool bSnapEveryTick = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger", meta=(ClampMin="0.0", ClampMax="2.0"))
    float MinReactionHoldTime = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Passenger", meta=(ClampMin="0.0", ClampMax="1.0"))
    float ReactionStrengthThreshold = 0.15f;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Passenger")
    FCarnivalReactionChangedSignature OnReactionChanged;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Passenger")
    FCarnivalBoardedSignature OnBoarded;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Passenger")
    FCarnivalUnboardedSignature OnUnboarded;

    UFUNCTION(BlueprintCallable, Category="Carnival|Passenger")
    bool BoardRide(AActor* RideActor, UCarnivalRideSeatComponent* Seat);

    UFUNCTION(BlueprintCallable, Category="Carnival|Passenger")
    void UnboardRide(const FTransform& ExitTransform, bool bDetachKeepWorld = true);

    UFUNCTION(BlueprintCallable, Category="Carnival|Passenger")
    void ApplyRideTelemetry(const FCarnivalRideTelemetry& Telemetry);

    UFUNCTION(BlueprintCallable, Category="Carnival|Passenger")
    void GeneratePersonality(int32 Seed);

    UFUNCTION(BlueprintPure, Category="Carnival|Passenger")
    bool IsRiding() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Passenger")
    UCarnivalRideSeatComponent* GetCurrentSeat() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Passenger")
    ECarnivalRideReaction GetCurrentReaction() const;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    ECarnivalRideReaction ChooseReaction(const FCarnivalRideTelemetry& Telemetry, float& OutStrength) const;
    void SetReaction(ECarnivalRideReaction NewReaction, float Strength, const FCarnivalRideTelemetry& Telemetry);

    UPROPERTY(Transient)
    TObjectPtr<AActor> CurrentRide = nullptr;

    UPROPERTY(Transient)
    TObjectPtr<UCarnivalRideSeatComponent> CurrentSeat = nullptr;

    UPROPERTY(Transient)
    ECarnivalRideReaction CurrentReaction = ECarnivalRideReaction::Calm;

    UPROPERTY(Transient)
    float LastReactionStrength = 0.0f;

    UPROPERTY(Transient)
    float LastReactionChangeTime = 0.0f;
};
