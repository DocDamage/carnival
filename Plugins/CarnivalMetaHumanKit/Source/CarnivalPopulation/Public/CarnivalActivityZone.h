#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalActivityZone.generated.h"

UENUM(BlueprintType)
enum class ECarnivalActivityType : uint8
{
    Wander,
    RideQueue,
    Food,
    GameBooth,
    Seating,
    Spectator,
    Exit
};

UCLASS(Blueprintable)
class CARNIVALPOPULATION_API ACarnivalActivityZone : public AActor
{
    GENERATED_BODY()

public:
    ACarnivalActivityZone();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Activity")
    ECarnivalActivityType ActivityType = ECarnivalActivityType::Wander;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Activity")
    FName ActivityId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Activity", meta=(ClampMin="1"))
    int32 Capacity = 8;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Activity", meta=(ClampMin="0.0"))
    float Weight = 1.0f;
};
