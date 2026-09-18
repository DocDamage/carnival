#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "CarnivalTypes.h"
#include "CarnivalPassengerInterface.generated.h"

UINTERFACE(Blueprintable)
class CARNIVALPOPULATION_API UCarnivalPassengerInterface : public UInterface
{
    GENERATED_BODY()
};

class CARNIVALPOPULATION_API ICarnivalPassengerInterface
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Carnival|Passenger")
    void CarnivalRideBoarded(AActor* RideActor, FName SeatId, ECarnivalRestraintType RestraintType);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Carnival|Passenger")
    void CarnivalRideReactionChanged(ECarnivalRideReaction Reaction, float Strength, const FCarnivalRideTelemetry& Telemetry);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Carnival|Passenger")
    void CarnivalRideUnboarded(AActor* RideActor);
};
