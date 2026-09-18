#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalTypes.h"
#include "CarnivalBlueprintLibrary.generated.h"

class UCarnivalRideSeatComponent;

UCLASS()
class CARNIVALPOPULATION_API UCarnivalBlueprintLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Carnival|Ride")
    static FTransform GetSeatIKTarget(const UCarnivalRideSeatComponent* Seat, FName TargetName);

    UFUNCTION(BlueprintPure, Category="Carnival|Ride")
    static float CalculateRideIntensity(float Speed, float Acceleration, float AngularSpeed, float SpeedMax = 1200.0f, float AccelMax = 2200.0f, float AngularMax = 180.0f);
};
