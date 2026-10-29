#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "CarnivalHovercraft.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalHovercraftTerrainJoinsTest,
    "Carnival.Vehicles.HovercraftTerrainJoins",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalHovercraftTerrainJoinsTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("HovercraftTerrainJoins"));
    UWorld* World = Instance->GetWorld();
    const FURL URL;
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();
    ON_SCOPE_EXIT
    {
        World->EndPlay(EEndPlayReason::Quit);
        Instance->Shutdown();
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    };

    auto Box = [World](const FVector& Location, const FVector& Extent, const FRotator& Rotation = FRotator::ZeroRotator)
    {
        auto* Actor = World->SpawnActor<AActor>();
        auto* Shape = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Shape);
        Shape->SetBoxExtent(Extent);
        Shape->SetCollisionProfileName(TEXT("BlockAll"));
        Shape->RegisterComponent();
        Actor->SetActorLocationAndRotation(Location, Rotation);
        return Actor;
    };
    auto Craft = [World](const FVector& Position, const FRotator& Rotation)
    {
        FActorSpawnParameters Spawn;
        Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Hover = World->SpawnActor<ACarnivalHovercraft>(Position, Rotation, Spawn);
        Hover->CollisionBox->SetBoxExtent(FVector(280, 205, 80)); // saved North Dock hull
        Hover->InputThrottle(.15f);
        return Hover;
    };

    auto* Upper = Box(FVector(-1000, 0, -20), FVector(1000, 800, 20));
    const float Angle = FMath::DegreesToRadians(21.0113286f);
    const FVector RampTop(1000.f * FMath::Cos(Angle), 0, -1000.f * FMath::Sin(Angle));
    const FVector RampNormal(FMath::Sin(Angle), 0, FMath::Cos(Angle));
    auto* Ramp = Box(RampTop - RampNormal * 20, FVector(1000, 800, 20), FRotator(-21.0113286f, 0, 0));

    auto* Descending = Craft(FVector(-500, 0, 100), FRotator::ZeroRotator);
    for (int32 Frame = 0; Frame < 180; ++Frame) Descending->Tick(1.f / 60.f);
    TestTrue(TEXT("Full-size hull crosses the convex pier/ramp join downhill"), Descending->GetActorLocation().X > 400);
    TestTrue(TEXT("Descending craft follows the ramp rather than staying at pier height"), Descending->GetActorLocation().Z < 0);
    Descending->Destroy();

    auto* Ascending = Craft(FVector(800, 0, 100 - 800 * FMath::Tan(Angle)), FRotator(21.0113286f, 180, 0));
    for (int32 Frame = 0; Frame < 240; ++Frame) Ascending->Tick(1.f / 60.f);
    TestTrue(TEXT("Craft returns up the ramp onto the flat pier"), Ascending->GetActorLocation().X < -200);
    TestTrue(TEXT("Returned craft settles at its normal hover height"), FMath::Abs(Ascending->GetActorLocation().Z - 100.f) < 3.f);
    Ascending->Destroy();
    Ramp->Destroy();
    Upper->Destroy();

    auto* Low = Box(FVector(-1000, 0, -20), FVector(1000, 800, 20));
    auto* Step = Box(FVector(1000, 0, 10), FVector(1000, 800, 20)); // 30 cm floating-deck step
    auto* Stepping = Craft(FVector(-500, 0, 100), FRotator::ZeroRotator);
    for (int32 Frame = 0; Frame < 180; ++Frame) Stepping->Tick(1.f / 60.f);
    AddInfo(FString::Printf(TEXT("Step final location=%s rotation=%s"), *Stepping->GetActorLocation().ToString(), *Stepping->GetActorRotation().ToString()));
    TestTrue(TEXT("Bow clears a 30 cm deck edge before the inset suspension rays reach it"), Stepping->GetActorLocation().X > 400);
    TestTrue(TEXT("Step exit restores the configured hover distance"), FMath::Abs(Stepping->GetActorLocation().Z - 130.f) < 3.f);
    Stepping->Destroy();
    Low->Destroy();
    Step->Destroy();

    auto* Flat = Box(FVector(0, 0, -20), FVector(2000, 800, 20));
    auto* Wall = Box(FVector(0, 0, 100), FVector(20, 800, 100));
    auto* Blocked = Craft(FVector(-500, 0, 100), FRotator::ZeroRotator);
    for (int32 Frame = 0; Frame < 180; ++Frame) Blocked->Tick(1.f / 60.f);
    TestTrue(TEXT("Clearance assistance does not lift the craft over a tall barrier"), Blocked->GetActorLocation().X < -250);
    TestTrue(TEXT("A blocked craft remains near its original hover height"), Blocked->GetActorLocation().Z < 150);
    Blocked->Destroy();
    Wall->Destroy();
    Flat->Destroy();

    auto* Unsupported = Craft(FVector(0, 0, 1000), FRotator::ZeroRotator);
    Unsupported->InputThrottle(0);
    Unsupported->Tick(.1f);
    TestTrue(TEXT("Clearance assistance does not create support over a void"), Unsupported->GetActorLocation().Z < 1000);
    return true;
}

#endif
