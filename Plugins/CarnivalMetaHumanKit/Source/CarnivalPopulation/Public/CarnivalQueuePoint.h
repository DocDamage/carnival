#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalQueuePoint.generated.h"

UCLASS(Blueprintable)
class CARNIVALPOPULATION_API ACarnivalQueuePoint : public AActor
{
    GENERATED_BODY()

public:
    ACarnivalQueuePoint();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Queue")
    FName RideId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Queue")
    int32 QueueIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Queue")
    float AcceptanceRadius = 65.0f;
};
