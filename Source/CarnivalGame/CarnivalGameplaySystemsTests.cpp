#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "CarnivalActivityBase.h"
#include "CarnivalTargetActor.h"
#include "CarnivalWeaponBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalMotorcycle.h"
#include "Components/SkeletalMeshComponent.h"
#include "CarnivalLadder.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "TimerManager.h"

namespace CarnivalGameplayTests
{
static AActor* Box(UWorld* World, const FVector& Location, const FVector& Extent)
{
    AActor* Actor = World->SpawnActor<AActor>();
    auto* Component = NewObject<UBoxComponent>(Actor);
    Actor->SetRootComponent(Component);
    Component->SetBoxExtent(Extent);
    Component->SetCollisionProfileName(TEXT("BlockAll"));
    Component->RegisterComponent();
    Actor->SetActorLocation(Location);
    return Actor;
}

static void BeginWorld(UWorld* World)
{
    const FURL URL;
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActivityLifecycleTest, "Carnival.Activities.LifecycleAndScoring",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FActivityLifecycleTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("ActivityLifecycle"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>();
    auto* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Player);
    auto* NPC = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(1000, 0, 0), FRotator::ZeroRotator);
    auto* Activity = World->SpawnActor<ACarnivalActivityBase>();
    auto* Target = World->SpawnActor<ACarnivalTargetActor>(FVector(500, 0, 100), FRotator::ZeroRotator);
    auto* Target2 = World->SpawnActor<ACarnivalTargetActor>(FVector(700, 0, 100), FRotator::ZeroRotator);
    auto* Foreign = World->SpawnActor<ACarnivalTargetActor>();
    Activity->Targets = {Target, Target2};
    Target->OwningActivity = Activity;
    Target2->OwningActivity = Activity;
    Target->OnCollectedOrHit(Player);
    TestFalse(TEXT("Inactive challenge target remains available"), Target->bIsHit);
    Activity->StartActivity(Player);
    Target->OnCollectedOrHit(NPC);
    TestFalse(TEXT("Crowd cannot consume player targets"), Target->bIsHit);
    Activity->OnTargetHit(Foreign);
    TestEqual(TEXT("Foreign target cannot score"), Activity->CurrentScore, 0);
    Target->OnCollectedOrHit(Player);
    Activity->OnTargetHit(Target);
    TestEqual(TEXT("Repeated hit scores once"), Activity->CurrentScore, Target->PointValue);
    Activity->StartActivity(Player);
    TestEqual(TEXT("Repeated start cannot erase progress"), Activity->CurrentScore, Target->PointValue);
    Target2->OnCollectedOrHit(Player);
    TestTrue(TEXT("All targets complete challenge"), Activity->ActivityState == ECarnivalActivityState::Completed);
    Activity->CompleteActivity(false);
    TestTrue(TEXT("Late callback cannot overwrite result"), Activity->ActivityState == ECarnivalActivityState::Completed);
    Activity->AbortActivity();
    TestFalse(TEXT("Cancel restores first target"), Target->bIsHit);
    TestFalse(TEXT("Cancel restores second target"), Target2->bIsHit);
    TestNull(TEXT("Cancel clears player activity"), Player->ActiveActivity);
    TestEqual(TEXT("Inactive challenge awards no medal"), Activity->GetMedalRating(), FString());
    TestTrue(TEXT("Reset restores authored target position"), Target->GetActorLocation().Equals(FVector(500, 0, 100)));

    Activity->Targets.Reset();
    Activity->Checkpoints.SetNum(2);
    Activity->Checkpoints[0].Location = FVector(10000, 0, 0);
    Activity->Checkpoints[1].Location = Player->GetActorLocation();
    Activity->TimeLimit = .1f;
    Activity->OnCheckpointReached(0);
    TestEqual(TEXT("Inactive checkpoint cannot score"), Activity->CurrentScore, 0);
    Activity->StartActivity(Player);
    Activity->OnCheckpointReached(1);
    TestEqual(TEXT("Out of order checkpoint is rejected"), Activity->CurrentCheckpointIndex, 0);
    Activity->OnCheckpointReached(0);
    Activity->OnCheckpointReached(0);
    TestEqual(TEXT("Duplicate checkpoint is rejected"), Activity->CurrentScore, 100);
    Activity->Tick(.1f);
    TestTrue(TEXT("Final checkpoint at deadline retains success"), Activity->ActivityState == ECarnivalActivityState::Completed);
    Activity->ResetActivity();
    Activity->StartActivity(Player);
    Activity->Tick(.2f);
    TestTrue(TEXT("Unfinished challenge expires"), Activity->ActivityState == ECarnivalActivityState::Failed);
    TestEqual(TEXT("Timer never becomes negative"), Activity->TimeRemaining, 0.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWeaponHitTest, "Carnival.Combat.HitDamageAndOcclusion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWeaponHitTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("WeaponHit"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>();
    auto* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Player);
    FVector Eye; FRotator Aim;
    Player->GetActorEyesViewPoint(Eye, Aim);
    auto* Target = World->SpawnActor<ACarnivalTargetActor>(Eye + FVector(150, 0, 0), FRotator::ZeroRotator);
    Target->TargetMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    Target->SetActorScale3D(FVector(.4f));
    auto* Weapon = World->SpawnActor<ACarnivalWeaponBase>();
    Weapon->WeaponType = ECarnivalWeaponType::Revolver;
    Weapon->PerformAttack(Player);
    TestTrue(TEXT("Revolver damages visible target"), Target->bIsHit);
    TestEqual(TEXT("Damage result is exposed for feedback"), Weapon->LastDamageDealt, Weapon->BaseDamage);
    Target->ResetTarget();
    Weapon->PerformAttack(Player);
    TestFalse(TEXT("Fire interval prevents repeated attack in same frame"), Target->bIsHit);
    Weapon->Destroy();
    Weapon = World->SpawnActor<ACarnivalWeaponBase>();
    Weapon->WeaponType = ECarnivalWeaponType::Sword;
    auto* Wall = CarnivalGameplayTests::Box(World, Eye + FVector(70, 0, 0), FVector(10, 100, 100));
    Weapon->PerformAttack(Player);
    TestFalse(TEXT("Melee cannot damage through blocking wall"), Target->bIsHit);
    Wall->Destroy();
    Weapon->Destroy();
    Weapon = World->SpawnActor<ACarnivalWeaponBase>();
    Weapon->WeaponType = ECarnivalWeaponType::Sword;
    Weapon->PerformAttack(Player);
    TestTrue(TEXT("Melee sweep damages reachable target"), Target->bIsHit);
    Target->ResetTarget();
    Weapon->Destroy();
    Player->PerformAttack();
    TestTrue(TEXT("Unarmed attack damages reachable target"), Target->bIsHit);
    Target->ResetTarget();
    Player->PerformAttack();
    TestFalse(TEXT("Unarmed cooldown prevents repeat hit"), Target->bIsHit);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBuildPlacementTest, "Carnival.Building.SupportedPlacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBuildPlacementTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("BuildPlacement"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 0, 100), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Player);
    Controller->SetControlRotation(FRotator(-20, 0, 0));
    auto* Build = Player->BuildComponent;
    Build->Categories.SetNum(1);
    Build->Categories[0].Pieces.Add(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    Build->ToggleBuildMode();
    TestFalse(TEXT("Cannot place unsupported piece in empty air"), Build->PlacePiece());
    CarnivalGameplayTests::Box(World, FVector(500, 0, -20), FVector(1000, 1000, 20));
    TestTrue(TEXT("Can place a supported clear piece"), Build->PlacePiece());
    TestTrue(TEXT("Mesh pivot is lifted above ground"), Build->CurrentHologramTransform.GetLocation().Z >= 50.f);
    // A solid obstruction intersects the candidate volume but leaves the ground trace clear.
    auto* Obstruction = CarnivalGameplayTests::Box(World, FVector(400, 70, 70), FVector(80, 60, 70));
    TestFalse(TEXT("Blocked placement is rejected"), Build->PlacePiece());
    Obstruction->Destroy();
    Build->CyclePiece(-100);
    TestEqual(TEXT("Negative cycle wraps safely"), Build->CurrentPieceIndex, 0);
    Build->Categories.AddDefaulted();
    Build->CycleCategory(1);
    TestFalse(TEXT("Empty category cannot use stale preview mesh"), Build->PlacePiece());
    Build->ToggleBuildMode();
    TestFalse(TEXT("Placement is disabled outside build mode"), Build->PlacePiece());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaterVehicleLifecycleTest, "Carnival.Vehicles.BoardingAndRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWaterVehicleLifecycleTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("WaterVehicleLifecycle"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    CarnivalGameplayTests::Box(World, FVector(0, 0, -20), FVector(10000, 10000, 20));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 215, 100), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Player);
    auto* Boat = World->SpawnActor<ACarnivalBoat>(FVector(0, 0, 100), FRotator::ZeroRotator);
    Boat->bAutoDetectWater = false;
    Boat->WaterPlaneZ = 100;
    Boat->WaveBobAmplitude = 0;
    Boat->MountTrigger->UpdateOverlaps();
    auto* BoardingWall = CarnivalGameplayTests::Box(World, FVector(0, 155, 160), FVector(500, 5, 160));
    TestFalse(TEXT("Boat boarding cannot pass through a wall"), Boat->CanMount(Player));
    Boat->Mount(Player);
    TestNull(TEXT("Blocked boarding leaves seat empty"), Boat->CurrentRider);
    BoardingWall->Destroy();
    TestTrue(TEXT("Player can board nearby stationary boat"), Boat->CanMount(Player));
    Boat->Mount(Player);
    TestTrue(TEXT("Controller possesses boat"), Controller->GetPawn() == Boat);
    TestTrue(TEXT("Rider collision disabled while seated"), Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
    TestTrue(TEXT("Boat camera follows controller look"), Boat->CameraBoom->bUsePawnControlRotation
        && Boat->CameraBoom->bInheritPitch && Boat->CameraBoom->bInheritYaw);
    auto* MountedActivity = World->SpawnActor<ACarnivalActivityBase>();
    FVector Eye; FRotator Aim;
    Player->GetActorEyesViewPoint(Eye, Aim);
    auto* MountedTarget = World->SpawnActor<ACarnivalTargetActor>(Eye + Aim.Vector() * 150.f, FRotator::ZeroRotator);
    MountedTarget->TargetMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    MountedTarget->SetActorScale3D(FVector(.4f));
    MountedActivity->Targets = {MountedTarget};
    MountedTarget->OwningActivity = MountedActivity;
    MountedActivity->StartActivity(Player);
    auto* MountedWeapon = World->SpawnActor<ACarnivalWeaponBase>();
    MountedWeapon->PerformAttack(Player);
    TestTrue(TEXT("Mounted rider weapon scores its active target"), MountedTarget->bIsHit);
    TestEqual(TEXT("Mounted target credits actual rider activity"), MountedActivity->CurrentScore, MountedTarget->PointValue);
    MountedActivity->AbortActivity();
    MountedTarget->OnCollectedOrHit(Boat);
    TestFalse(TEXT("Possessed vehicle cannot score an inactive target"), MountedTarget->bIsHit);
    MountedTarget->Destroy(); MountedWeapon->Destroy(); MountedActivity->Destroy();
    Boat->CurrentSpeed = 200;
    Boat->Dismount();
    TestTrue(TEXT("Boat cannot eject moving rider"), Controller->GetPawn() == Boat);
    Boat->CurrentSpeed = 0;
    Boat->Dismount();
    TestTrue(TEXT("Boat exit returns possession"), Controller->GetPawn() == Player);
    TestTrue(TEXT("Boat exit restores capsule collision"), Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
    TestTrue(TEXT("Boat exit lies beyond hull"), FMath::Abs(Player->GetActorLocation().Y) > 160.f);
    Player->SetActorLocation(FVector(0, 190, 100));
    Boat->MountTrigger->UpdateOverlaps();
    Boat->Mount(Player);
    Boat->InputThrottle(1);
    Boat->Destroy();
    TestTrue(TEXT("Destroying boat restores rider possession"), Controller->GetPawn() == Player);
    TestNull(TEXT("Destroyed boat no longer mounted"), Player->MountedBoat);

    Player->SetActorLocation(FVector(2000, 240, 100));
    auto* Hover = World->SpawnActor<ACarnivalHovercraft>(FVector(2000, 0, 100), FRotator::ZeroRotator);
    Hover->MountTrigger->UpdateOverlaps();
    BoardingWall = CarnivalGameplayTests::Box(World, FVector(2000, 190, 160), FVector(500, 3, 160));
    TestFalse(TEXT("Hovercraft boarding cannot pass through a wall"), Hover->CanMount(Player));
    BoardingWall->Destroy();
    TestTrue(TEXT("Player can board nearby hovercraft"), Hover->CanMount(Player));
    Hover->Mount(Player);
    TestTrue(TEXT("Controller possesses hovercraft"), Controller->GetPawn() == Hover);
    TestTrue(TEXT("Hovercraft camera follows controller look"), Hover->CameraBoom->bUsePawnControlRotation
        && Hover->CameraBoom->bInheritPitch && Hover->CameraBoom->bInheritYaw);
    Hover->InputThrottle(1);
    Hover->InputStrafe(1);
    Hover->InputBoost(true);
    Controller->UnPossess();
    World->GetTimerManager().Tick(.01f);
    TestTrue(TEXT("Unexpected possession loss recovers hover rider"), Controller->GetPawn() == Player);
    TestFalse(TEXT("Recovery clears boost"), Hover->bIsBoosting);
    TestTrue(TEXT("Recovery restores walking"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking);
    const FVector Before = Hover->GetActorLocation();
    Hover->Tick(.1f);
    TestTrue(TEXT("Recovered hovercraft has no held movement"), FVector::Dist2D(Before, Hover->GetActorLocation()) < 1.f);
    Hover->SetActorLocation(FVector(2000, 0, 2000));
    Hover->Tick(.1f);
    TestTrue(TEXT("Hovercraft falls when support is absent"), Hover->GetActorLocation().Z < 2000.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FParkourTraversalTest, "Carnival.Parkour.ClearanceTraversalAndLadder",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FParkourTraversalTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("ParkourTraversal"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    CarnivalGameplayTests::Box(World, FVector(0, 0, -20), FVector(2000, 2000, 20));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 0, 98), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Player);
    auto Finish = [&] { for (int32 I = 0; I < 600 && Player->IsParkourTraversing(); ++I) Player->Tick(1.f / 60.f); };
    auto Reset = [&] { Player->CancelParkourTraversal(); Player->SetActorLocation(FVector(0, 0, 98));
        Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking); };
    auto* Obstacle = CarnivalGameplayTests::Box(World, FVector(140, 0, 50), FVector(40, 100, 50));
    for (int32 I = 0; I < 10; ++I) World->Tick(LEVELTICK_All, .02f);
    TestTrue(TEXT("Player has settled onto the fixture floor"), Player->GetCharacterMovement()->IsMovingOnGround());
    TestTrue(TEXT("Low obstacle starts a vault"), Player->TryVaultOrMantle());
    TestTrue(TEXT("Vault keeps physical capsule enabled"), Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
    Finish();
    TestFalse(TEXT("Vault finishes traversal"), Player->IsParkourTraversing());
    TestTrue(TEXT("Vault lands beyond obstacle"), Player->GetActorLocation().X > 250.f);
    TestTrue(TEXT("Vault restores walking"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking);
    Reset();
    auto* Ceiling = CarnivalGameplayTests::Box(World, FVector(80, 0, 220), FVector(150, 150, 10));
    TestFalse(TEXT("Low ceiling prevents vault"), Player->TryVaultOrMantle());
    Ceiling->Destroy();
    TestTrue(TEXT("Vault resumes when ceiling removed"), Player->TryVaultOrMantle());
    auto* Intruder = CarnivalGameplayTests::Box(World, FVector(220, 0, 170), FVector(20, 100, 150));
    Finish();
    TestFalse(TEXT("New obstruction cancels traversal"), Player->IsParkourTraversing());
    TestTrue(TEXT("Collision stops player before new obstacle"), Player->GetActorLocation().X < 180.f);
    TestTrue(TEXT("Interrupted traversal restores active movement"), Player->GetCharacterMovement()->MovementMode != MOVE_None);
    Intruder->Destroy();
    Obstacle->Destroy();
    Reset();
    auto* Platform = CarnivalGameplayTests::Box(World, FVector(250, 0, 80), FVector(150, 100, 80));
    TestTrue(TEXT("High ledge starts a mantle"), Player->TryVaultOrMantle());
    Finish();
    TestTrue(TEXT("Mantle reaches ledge top"), Player->GetActorLocation().Z > 250.f);
    TestTrue(TEXT("Mantle restores walking"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking);
    Platform->Destroy();
    Reset();
    auto* UpperFloor = CarnivalGameplayTests::Box(World, FVector(220, 0, 280), FVector(80, 100, 20));
    auto* Ladder = World->SpawnActor<ACarnivalLadder>();
    Ladder->TopExit->SetRelativeLocation(FVector(220, 0, 300));
    TestTrue(TEXT("Authored ladder starts ascent"), Player->TryLadderClimb());
    Finish();
    TestTrue(TEXT("Ladder reaches upper exit"), Player->GetActorLocation().Equals(FVector(220, 0, 399), 1.f));
    TestTrue(TEXT("Ladder starts descent from upper exit"), Player->TryLadderClimb());
    Finish();
    TestTrue(TEXT("Ladder returns to lower exit"), Player->GetActorLocation().Equals(FVector(0, 0, 99), 1.f));
    TestTrue(TEXT("Ladder can be reused"), Player->TryLadderClimb());
    Player->Tick(.25f);
    Player->CancelParkourTraversal();
    TestFalse(TEXT("Cancel clears ladder state"), Player->IsParkourTraversing());
    TestTrue(TEXT("Cancel allows falling to safety"), Player->GetCharacterMovement()->MovementMode == MOVE_Falling);
    UpperFloor->Destroy();
    Reset();
    TestFalse(TEXT("Ladder without supported upper exit is refused"), Player->TryLadderClimb());
    Player->ToggleProne();
    TestTrue(TEXT("Prone preserves floor contact"), FMath::IsNearlyEqual(Player->GetActorLocation().Z
        - Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), 2.f, 1.f));
    Ceiling = CarnivalGameplayTests::Box(World, FVector(0, 0, 100), FVector(100, 100, 10));
    Player->ToggleProne();
    TestEqual(TEXT("Low ceiling prevents standing from prone"), Player->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(), 30.f);
    Ceiling->Destroy();
    Player->ToggleProne();
    TestEqual(TEXT("Cleared ceiling permits standing"), Player->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(), 96.f);
    TestTrue(TEXT("Standing preserves floor contact"), FMath::IsNearlyEqual(Player->GetActorLocation().Z, 98.f, 1.f));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChaosMotorcycleControlsTest, "Carnival.Motorcycle.ChaosControlsAndModeTransition",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FChaosMotorcycleControlsTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("ChaosMotorcycleControls"));
    UWorld* World = Instance->GetWorld();
    CarnivalGameplayTests::BeginWorld(World);
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* BareBike = World->SpawnActor<ACarnivalMotorcycle>();
    BareBike->SetPhysicsMode(EMotorcyclePhysicsMode::ChaosPhysics);
    TestTrue(TEXT("Missing physics body retains arcade mode"), BareBike->PhysicsMode == EMotorcyclePhysicsMode::Arcade);
    BareBike->Destroy();
    CarnivalGameplayTests::Box(World, FVector(0, 0, -20), FVector(10000, 10000, 20));
    UClass* BikeClass = LoadClass<ACarnivalMotorcycle>(nullptr,
        TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    if (!TestNotNull(TEXT("Authored motorcycle class exists"), BikeClass)) return false;
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>(BikeClass, FVector(0, 0, 20), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Authored motorcycle spawned"), Bike)) return false;
    Bike->SetActorTickEnabled(false);
    Bike->CurrentSpeed = 900.f;
    Bike->SetPhysicsMode(EMotorcyclePhysicsMode::ChaosPhysics);
    if (!TestTrue(TEXT("Authored body simulates Chaos"), Bike->BikeMesh->IsSimulatingPhysics())) return false;
    TestTrue(TEXT("Entering Chaos preserves forward speed"), FMath::IsNearlyEqual(Bike->BikeMesh->GetPhysicsLinearVelocity().X, 900.f, 1.f));
    // Isolate the input forces from suspension/tipping acceptance: the real
    // authored chassis simulates, with gravity disabled above a probe floor.
    Bike->BikeMesh->SetEnableGravity(false);
    // The engine tick task manager visits each physics tick once per frame.
    // Standalone synchronous automation must advance this just like the engine loop.
    auto Step = [&] { ++GFrameCounter; Bike->Tick(.02f); World->Tick(LEVELTICK_All, .02f); };
    Bike->InputThrottle(1.f);
    Bike->InputBrake(1.f);
    for (int32 I = 0; I < 35; ++I) Step();
    TestTrue(FString::Printf(TEXT("Chaos brake overrules held throttle (speed %.2f)"), Bike->BikeMesh->GetPhysicsLinearVelocity().X), FMath::Abs(Bike->BikeMesh->GetPhysicsLinearVelocity().X) < 20.f);
    TestFalse(TEXT("Floor probes detect grounded bike"), Bike->bIsAirborne);
    TestTrue(TEXT("Chaos travel turns wheel visuals"), FMath::Abs(Bike->FrontWheel->GetRelativeRotation().Pitch) > 1.f);
    Bike->InputBrake(0.f);
    Bike->InputBrakeReverse(.5f);
    Bike->BikeMesh->SetPhysicsLinearVelocity(FVector(200, 0, 0));
    bool bStopped = false;
    bool bReversedBeforeStopping = false;
    for (int32 I = 0; I < 100; ++I)
    {
        Step();
        const float Speed = Bike->BikeMesh->GetPhysicsLinearVelocity().X;
        if (FMath::Abs(Speed) <= 2.f) bStopped = true;
        if (Speed < -2.f && !bStopped) bReversedBeforeStopping = true;
    }
    TestTrue(TEXT("L2 brakes to zero before reversing"), bStopped && !bReversedBeforeStopping);
    TestTrue(FString::Printf(TEXT("Analog reverse limits speed despite forward trigger (speed %.2f, limit %.2f)"), Bike->BikeMesh->GetPhysicsLinearVelocity().X, Bike->ReverseSpeed * .5f),
        Bike->BikeMesh->GetPhysicsLinearVelocity().X < -100.f
        && Bike->BikeMesh->GetPhysicsLinearVelocity().X >= -Bike->ReverseSpeed * .5f - 20.f);
    Bike->InputBrakeReverse(0.f);
    Bike->InputHandbrake(true);
    Bike->BikeMesh->SetPhysicsLinearVelocity(FVector(500, 0, 0));
    for (int32 I = 0; I < 40; ++I) Step();
    TestTrue(FString::Printf(TEXT("Handbrake stops held Chaos throttle (speed %.2f)"), Bike->BikeMesh->GetPhysicsLinearVelocity().X), FMath::Abs(Bike->BikeMesh->GetPhysicsLinearVelocity().X) < 20.f);
    Bike->InputHandbrake(false);
    Bike->SetActorLocationAndRotation(FVector(0, 0, 2000), FRotator::ZeroRotator, false, nullptr, ETeleportType::TeleportPhysics);
    Bike->BikeMesh->SetPhysicsLinearVelocity(FVector::ZeroVector);
    Bike->InputBrakeReverse(1.f);
    for (int32 I = 0; I < 10; ++I) Step();
    TestTrue(TEXT("Airborne Chaos bike has no ground traction"), Bike->bIsAirborne && Bike->BikeMesh->GetPhysicsLinearVelocity().Size2D() < 1.f);
    Bike->BikeMesh->SetPhysicsLinearVelocity(FVector(350, 0, 120));
    Bike->SetPhysicsMode(EMotorcyclePhysicsMode::Arcade);
    TestFalse(TEXT("Returning to arcade disables body simulation"), Bike->BikeMesh->IsSimulatingPhysics());
    TestTrue(TEXT("Returning to arcade preserves motion"), FMath::IsNearlyEqual(Bike->CurrentSpeed, 350.f, 1.f)
        && FMath::IsNearlyEqual(Bike->VerticalVelocity, 120.f, 1.f));
    return true;
}

#endif
