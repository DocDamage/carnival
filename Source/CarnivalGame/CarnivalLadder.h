#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalLadder.generated.h"

class USceneComponent;

/** Author the two markers on clear, walkable floor at each end of a ladder. */
UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalLadder : public AActor
{
    GENERATED_BODY()
public:
    ACarnivalLadder();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ladder")
    TObjectPtr<USceneComponent> BottomExit;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ladder")
    TObjectPtr<USceneComponent> TopExit;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ladder", meta = (ClampMin = "25"))
    float InteractionDistance = 160.f;
};
