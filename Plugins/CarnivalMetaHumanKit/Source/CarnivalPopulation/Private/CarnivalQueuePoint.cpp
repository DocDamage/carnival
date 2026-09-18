#include "CarnivalQueuePoint.h"
#include "Components/SceneComponent.h"

ACarnivalQueuePoint::ACarnivalQueuePoint()
{
    PrimaryActorTick.bCanEverTick = false;
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
}
