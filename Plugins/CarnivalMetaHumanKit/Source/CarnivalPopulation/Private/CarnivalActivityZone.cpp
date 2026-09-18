#include "CarnivalActivityZone.h"
#include "Components/SceneComponent.h"

ACarnivalActivityZone::ACarnivalActivityZone()
{
    PrimaryActorTick.bCanEverTick = false;
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
}
