#include "CarnivalLadder.h"
#include "Components/SceneComponent.h"

ACarnivalLadder::ACarnivalLadder()
{
    PrimaryActorTick.bCanEverTick = false;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
    BottomExit = CreateDefaultSubobject<USceneComponent>(TEXT("BottomExit"));
    BottomExit->SetupAttachment(RootComponent);
    TopExit = CreateDefaultSubobject<USceneComponent>(TEXT("TopExit"));
    TopExit->SetupAttachment(RootComponent);
    TopExit->SetRelativeLocation(FVector(160, 0, 300));
}
