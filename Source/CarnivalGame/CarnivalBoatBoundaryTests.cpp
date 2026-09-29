#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "CarnivalBoat.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalBoatWaterBoundaryTest,
    "Carnival.Vehicles.BoatSurveyedWaterBoundary",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalBoatWaterBoundaryTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("BoatWaterBoundary"));
    UWorld* World = Instance->GetWorld();
    const FURL URL;
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Boat = World->SpawnActor<ACarnivalBoat>();
    Boat->WaveBobAmplitude = 0.f;
    TestTrue(TEXT("Legacy placements remain opt-in"), Boat->IsWaterTransformNavigable(FVector(100000,0,0), FRotator::ZeroRotator));
    Boat->bUseNavigableWaterBounds = true;
    TestFalse(TEXT("Invalid empty region fails closed"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator::ZeroRotator));
    Boat->NavigableWaterMin = FVector2D(-1000,-1000);
    Boat->NavigableWaterMax = FVector2D(1000,1000);
    TestTrue(TEXT("Surveyed deep open water permits hull"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator::ZeroRotator));
    TestFalse(TEXT("Bow crossing boundary is rejected before center crosses"), Boat->IsWaterTransformNavigable(FVector(750,0,0), FRotator::ZeroRotator));
    Boat->NavigableWaterMin = FVector2D(-350,-150);
    Boat->NavigableWaterMax = FVector2D(350,150);
    TestTrue(TEXT("Hull fits measured straight berth"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator::ZeroRotator));
    TestFalse(TEXT("Rotated hull corners cannot cross bank"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator(0,90,0)));
    Boat->NavigableWaterMin = FVector2D(-1000,-1000);
    Boat->NavigableWaterMax = FVector2D(1000,1000);

    auto* Ground = World->SpawnActor<AActor>();
    auto* Box = NewObject<UBoxComponent>(Ground);
    Ground->SetRootComponent(Box); Box->SetBoxExtent(FVector(1000,1000,10));
    Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent();
    Ground->SetActorLocation(FVector(0,0,-100));
    TestFalse(TEXT("Shallow bottom inside keel clearance is rejected"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator::ZeroRotator));
    Ground->SetActorLocation(FVector(0,0,-140));
    TestTrue(TEXT("Sufficient bottom clearance permits navigation"), Boat->IsWaterTransformNavigable(FVector::ZeroVector, FRotator::ZeroRotator));
    Ground->Destroy();

    Boat->InputThrottle(1.f);
    for (int32 I=0; I<120; ++I) Boat->Tick(1.f/30.f);
    TestTrue(TEXT("Powered movement stops with entire hull inside region"), Boat->GetActorLocation().X <= 700.1f && Boat->GetActorLocation().X > 500.f);
    TestEqual(TEXT("Boundary collision stops forward speed"), Boat->CurrentSpeed, 0.f);
    const float StoppedX=Boat->GetActorLocation().X;
    Boat->InputThrottle(-1.f);
    for (int32 I=0; I<20; ++I) Boat->Tick(1.f/30.f);
    TestTrue(TEXT("Player can reverse away from rejected boundary"), Boat->GetActorLocation().X < StoppedX-50.f);
    return true;
}
#endif
