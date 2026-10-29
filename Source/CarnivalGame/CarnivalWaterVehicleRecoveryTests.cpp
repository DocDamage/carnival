#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "CarnivalActivityBase.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"

namespace WaterRecoveryTests
{
static AActor* Box(UWorld* World, FVector Position, FVector Extent)
{
    auto* Actor = World->SpawnActor<AActor>();
    auto* Component = NewObject<UBoxComponent>(Actor);
    Actor->SetRootComponent(Component);
    Component->SetBoxExtent(Extent);
    Component->SetCollisionProfileName(TEXT("BlockAll"));
    Component->RegisterComponent();
    Actor->SetActorLocation(Position);
    return Actor;
}
static void Begin(UWorld* World)
{
    const FURL URL;
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaterMountedRecoveryTest, "Carnival.Vehicles.MountedBoardingPointRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWaterMountedRecoveryTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MountedBoardingRecovery"));
    UWorld* World = Instance->GetWorld();
    WaterRecoveryTests::Begin(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Floor = WaterRecoveryTests::Box(World, FVector(0, 0, -20), FVector(5000, 5000, 20));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 200, 98), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<ACarnivalPlayerController>();
    Controller->Possess(Player);
    Player->GetMesh()->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
    auto* Boat = World->SpawnActor<ACarnivalBoat>(FVector(0, 0, 200), FRotator::ZeroRotator);
    Boat->bAutoDetectWater = false;
    Boat->WaterPlaneZ = 200;
    Boat->WaveBobAmplitude = 0;
    Boat->bUseNavigableWaterBounds = true;
    Boat->NavigableWaterMin = FVector2D(-1000, -1000);
    Boat->NavigableWaterMax = FVector2D(1000, 1000);
    Boat->MountTrigger->UpdateOverlaps();
    Boat->Mount(Player);
    TestTrue(TEXT("Fixture boards boat through the real mount policy"), Boat->CurrentRider == Player);
    TestEqual(TEXT("Mounted rider mesh does not collapse the boat camera"), Player->GetMesh()->GetCollisionResponseToChannel(ECC_Camera), ECR_Ignore);
    auto* Activity = World->SpawnActor<ACarnivalActivityBase>();
    Activity->StartActivity(Player);
    Boat->InputThrottle(.2f);
    for (int32 Frame = 0; Frame < 360; ++Frame) Boat->Tick(1.f / 60.f);
    TestTrue(TEXT("Sustained powered boundary rejection offers recovery"), Boat->CanRecoverToBoardingPoint());
    const FVector Stopped = Boat->GetActorLocation();
    auto* BerthBlocker = WaterRecoveryTests::Box(World, FVector(0, 0, 200), FVector(150, 150, 150));
    TestFalse(TEXT("Occupied boarding hull cannot be used as a recovery destination"), Boat->TryRecoverToBoardingPoint());
    TestTrue(TEXT("Rejected recovery preserves position and active challenge"), Boat->GetActorLocation().Equals(Stopped, .1f)
        && Activity->ActivityState == ECarnivalActivityState::Active);
    BerthBlocker->Destroy();
    Boat->Dismount(); // the same contextual action used by keyboard/gamepad
    TestTrue(TEXT("Recovery action returns boat while keeping possession and rider attachment"),
        Controller->GetPawn() == Boat && Player->MountedBoat == Boat && Boat->GetActorLocation().Equals(FVector(0, 0, 200), .1f));
    TestTrue(TEXT("Recovery cancels the challenge instead of skipping checkpoints"),
        Activity->ActivityState == ECarnivalActivityState::Inactive && !Player->ActiveActivity);
    TestEqual(TEXT("Recovered rider retains seated collision policy"), Player->GetCapsuleComponent()->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
    TestEqual(TEXT("Recovery retains rider camera ignore"), Player->GetMesh()->GetCollisionResponseToChannel(ECC_Camera), ECR_Ignore);
    for (int32 Frame = 0; Frame < 30; ++Frame) Boat->Tick(1.f / 60.f);
    TestTrue(TEXT("Held throttle was cleared"), Boat->GetActorLocation().Equals(FVector(0, 0, 200), .1f));
    Boat->Dismount();
    TestTrue(TEXT("Next ordinary exit restores walking possession"), Controller->GetPawn() == Player
        && Player->GetCharacterMovement()->MovementMode == MOVE_Walking);
    TestEqual(TEXT("Boat exit restores the original rider camera response"), Player->GetMesh()->GetCollisionResponseToChannel(ECC_Camera), ECR_Block);

    Player->SetActorLocation(FVector(3000, 230, 98));
    Player->GetMesh()->SetCollisionResponseToChannel(ECC_Camera, ECR_Overlap);
    auto* Hover = World->SpawnActor<ACarnivalHovercraft>(FVector(3000, 0, 100), FRotator::ZeroRotator);
    Hover->MountTrigger->UpdateOverlaps();
    Hover->Mount(Player);
    TestTrue(TEXT("Fixture boards hovercraft"), Hover->CurrentRider == Player);
    TestEqual(TEXT("Mounted rider mesh does not collapse the hovercraft camera"), Player->GetMesh()->GetCollisionResponseToChannel(ECC_Camera), ECR_Ignore);
    Hover->SetActorLocation(FVector(20000, 0, 1000)); // unsupported fixture, no recovery destination there
    Hover->InputThrottle(.3f);
    Hover->InputStrafe(.3f);
    Hover->InputBoost(true);
    for (int32 Frame = 0; Frame < 360; ++Frame) Hover->Tick(1.f / 60.f);
    TestTrue(TEXT("Deep unsupported fall returns the mounted craft to its supported boarding point"),
        Hover->GetActorLocation().Equals(FVector(3000, 0, 100), 3.f) && Controller->GetPawn() == Hover && Player->MountedHovercraft == Hover);
    TestFalse(TEXT("Automatic recovery clears boost"), Hover->bIsBoosting);
    TestTrue(TEXT("Automatic recovery clears forward and strafe motion"),
        FMath::IsNearlyZero(Hover->CurrentForwardSpeed) && FMath::IsNearlyZero(Hover->CurrentStrafeSpeed));
    Hover->InputThrottle(.3f); Hover->InputStrafe(.3f);
    for (int32 Frame = 0; Frame < 30; ++Frame) Hover->Tick(1.f / 60.f);
    TestTrue(TEXT("Brake fixture is moving forward and sideways"), Hover->CurrentForwardSpeed > 100 && Hover->CurrentStrafeSpeed > 100);
    Hover->InputBrake(1.f);
    for (int32 Frame = 0; Frame < 180; ++Frame) Hover->Tick(1.f / 60.f);
    TestTrue(TEXT("Hover brake overcomes held throttle and strafe"), FMath::Abs(Hover->CurrentForwardSpeed) < 1 && FMath::Abs(Hover->CurrentStrafeSpeed) < 1);
    TestFalse(TEXT("Intentional braking does not offer stuck recovery"), Hover->CanRecoverToBoardingPoint());
    Hover->InputBrake(0.f);
    for (int32 Frame = 0; Frame < 20; ++Frame) Hover->Tick(1.f / 60.f);
    TestTrue(TEXT("Releasing brake resumes held movement"), Hover->CurrentForwardSpeed > 100 && Hover->CurrentStrafeSpeed > 100);
    Hover->ClearControlInputs();
    Hover->CurrentForwardSpeed = Hover->CurrentStrafeSpeed = 0;
    Hover->SetActorLocation(FVector(3000, 0, 100));
    auto* Wall = WaterRecoveryTests::Box(World, FVector(3500, 0, 100), FVector(20, 800, 100));
    Hover->InputThrottle(.3f);
    for (int32 Frame = 0; Frame < 360; ++Frame) Hover->Tick(1.f / 60.f);
    TestTrue(TEXT("Blocked hovercraft offers manual recovery"), Hover->CanRecoverToBoardingPoint());
    Hover->Dismount();
    TestTrue(TEXT("Manual hovercraft recovery preserves the seated rider"), Controller->GetPawn() == Hover
        && Hover->GetActorLocation().Equals(FVector(3000, 0, 100), .1f));
    Wall->Destroy();
    Hover->Dismount();
    TestTrue(TEXT("Ordinary hovercraft exit restores player possession"), Controller->GetPawn() == Player);
    TestEqual(TEXT("Hovercraft exit restores the distinct original camera response"), Player->GetMesh()->GetCollisionResponseToChannel(ECC_Camera), ECR_Overlap);
    Player->SetActorLocation(FVector(3000, 230, 98));
    Hover->MountTrigger->UpdateOverlaps(); Hover->Mount(Player);
    TestTrue(TEXT("Hovercraft reboards before unsupported destination probe"), Hover->CurrentRider == Player);
    Floor->Destroy();
    Hover->SetActorLocation(FVector(20000, 0, 1000));
    for (int32 Frame = 0; Frame < 180; ++Frame) Hover->Tick(1.f / 60.f);
    TestFalse(TEXT("Removed support at boarding point prevents an unsafe recovery"), Hover->TryRecoverToBoardingPoint());
    TestTrue(TEXT("Rejected unsupported destination leaves the rider possessed"), Controller->GetPawn() == Hover);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMountedActivityControlsTest, "Carnival.Input.MountedActivityControls",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMountedActivityControlsTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MountedActivityInput"));
    UWorld* World = Instance->GetWorld();
    WaterRecoveryTests::Begin(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    WaterRecoveryTests::Box(World, FVector(0, 0, -20), FVector(5000, 5000, 20));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 200, 98), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<ACarnivalPlayerController>();
    Controller->Possess(Player);
    auto* Boat = World->SpawnActor<ACarnivalBoat>(FVector(0, 0, 100), FRotator::ZeroRotator);
    Boat->MountTrigger->UpdateOverlaps(); Boat->Mount(Player);
    auto* Activity = World->SpawnActor<ACarnivalActivityBase>();
    auto Check = [&](APawn* Vehicle)
    {
        Activity->StartActivity(Player);
        Activity->CompleteActivity(true);
        Controller->OnContextInteract();
        TestTrue(TEXT("Mapped context handler dismisses a mounted completion"),
            Activity->ActivityState == ECarnivalActivityState::Inactive && !Player->ActiveActivity && Controller->GetPawn() == Vehicle);
        Activity->StartActivity(Player);
        Controller->OnCancel();
        TestTrue(TEXT("Mapped cancel handler aborts a mounted activity without ejecting the rider"),
            Activity->ActivityState == ECarnivalActivityState::Inactive && !Player->ActiveActivity && Controller->GetPawn() == Vehicle);
        Activity->StartActivity(Player); Activity->CompleteActivity(false);
        Controller->OnContextInteract();
        TestTrue(TEXT("Mapped context handler also dismisses a mounted failure"), !Player->ActiveActivity
            && Activity->ActivityState == ECarnivalActivityState::Inactive && Controller->GetPawn() == Vehicle);
    };
    Check(Boat);
    Boat->Dismount();
    Player->SetActorLocation(FVector(2000, 230, 98));
    auto* Hover = World->SpawnActor<ACarnivalHovercraft>(FVector(2000, 0, 100), FRotator::ZeroRotator);
    Hover->MountTrigger->UpdateOverlaps(); Hover->Mount(Player);
    Check(Hover);
    return true;
}

#endif
