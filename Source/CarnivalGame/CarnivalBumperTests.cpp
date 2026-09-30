#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "CarnivalBumperArenaComponent.h"
#include "CarnivalBumperCar.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalRideControllerComponent.h"
#include "CarnivalRideOperationComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "GameFramework/PlayerController.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalBumperDrivingTest, "Carnival.Rides.BumperDrivingAndHandover",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalBumperDrivingTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("BumperDriving"));
    UWorld* World = Instance->GetWorld();
    const FURL URL;
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto Box = [World](FVector Position, FVector Extent)
    {
        auto* Actor = World->SpawnActor<AActor>();
        auto* Body = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Body); Body->SetBoxExtent(Extent); Body->SetCollisionProfileName(TEXT("BlockAll"));
        Body->RegisterComponent(); Actor->SetActorLocation(Position); return Actor;
    };
    Box(FVector(0, 0, -20), FVector(5000, 5000, 20));
    auto* Ride = World->SpawnActor<AActor>();
    auto* Root = NewObject<USceneComponent>(Ride);
    Ride->SetRootComponent(Root); Root->RegisterComponent();
    auto* RideController = NewObject<UCarnivalRideControllerComponent>(Ride);
    Ride->AddInstanceComponent(RideController); RideController->RegisterComponent();
    auto* Arena = NewObject<UCarnivalBumperArenaComponent>(Ride);
    Ride->AddInstanceComponent(Arena); Arena->RegisterComponent(); Arena->HalfExtent = FVector2D(700, 700);
    auto* Car = World->SpawnActor<ACarnivalBumperCar>(FVector(0, 0, 36), FRotator::ZeroRotator);
    Arena->Cars.Add(Car);
    auto* DisplayCar = NewObject<UStaticMeshComponent>(Ride, TEXT("ReplacedDisplayCar"));
    Ride->AddInstanceComponent(DisplayCar); DisplayCar->RegisterComponent();
    DisplayCar->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    auto* Platform = NewObject<UStaticMeshComponent>(Ride, TEXT("ArenaPlatform"));
    Ride->AddInstanceComponent(Platform); Platform->RegisterComponent();
    Platform->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Arena->ReplacedDisplayCarComponents.Add(DisplayCar->GetFName());
    auto* Operation = NewObject<UCarnivalRideOperationComponent>(Ride);
    Ride->AddInstanceComponent(Operation);
    Operation->Experience = ECarnivalRideExperience::DrivingArena;
    Operation->Attendant = World->SpawnActor<AActor>();
    auto* AttendantRoot = NewObject<USceneComponent>(Operation->Attendant);
    Operation->Attendant->SetRootComponent(AttendantRoot); AttendantRoot->RegisterComponent();
    Operation->Attendant->SetActorLocation(FVector(-300, 0, 96));
    Operation->BoardingSeconds = Operation->SecuringSeconds = Operation->UnloadingSeconds = .1f;
    Operation->CycleSeconds = 30.f;
    Operation->RegisterComponent();
    TestTrue(TEXT("Driving arena initializes without vendor start functions or fixed seats"), Operation->InitializeOperation());
    TestTrue(TEXT("Retired display collision restored by Blueprint is removed on initialization"),
        DisplayCar->GetCollisionEnabled() == ECollisionEnabled::NoCollision && DisplayCar->bHiddenInGame && !DisplayCar->IsVisible());
    TestTrue(TEXT("Replacement cleanup preserves platform collision and visibility"),
        Platform->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics && Platform->IsVisible());
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(-300, 0, 98), FRotator::ZeroRotator);
    auto* Controller = World->SpawnActor<APlayerController>(); Controller->Possess(Player);
    auto Tick = [&] { ++GFrameCounter; World->Tick(LEVELTICK_All, 1.f/60.f); };
    auto* ApproachWall = Box(FVector(-140, 0, 120), FVector(10, 200, 120));
    TestFalse(TEXT("Arena cannot board through a wall"), Operation->RequestBoard(Player));
    ApproachWall->Destroy();
    if (!TestTrue(TEXT("Attendant boards available driver seat"), Operation->RequestBoard(Player))) return false;
    TestTrue(TEXT("Controller transfers to bumper car"), Controller->GetPawn() == Car);
    TestTrue(TEXT("Passenger remains attached with riding state"), Player->RidePassenger->IsRiding());
    Car->InputThrottle(1.f);
    for (int32 I=0; I<5; ++I) Tick();
    TestTrue(TEXT("Loading locks propulsion"), FMath::Abs(Car->CurrentSpeed) < 1.f);
    for (int32 I=0; I<45; ++I) Tick();
    TestTrue(TEXT("Staff cycle enables player driving"), Operation->State == ECarnivalOperationState::Running && Car->GetActorLocation().X > 30.f);
    Car->InputBrake(1.f);
    for (int32 I=0; I<45; ++I) Tick();
    TestTrue(TEXT("Brake overrides throttle"), Car->IsStopped());
    Car->InputBrake(0.f); Car->InputSteering(1.f);
    const float PreviousYaw = Car->GetActorRotation().Yaw;
    for (int32 I=0; I<30; ++I) Tick();
    TestTrue(TEXT("Steering changes heading"), FMath::Abs(FMath::FindDeltaAngleDegrees(PreviousYaw, Car->GetActorRotation().Yaw)) > 5.f);
    for (int32 I=0; I<240; ++I) Tick();
    TestTrue(TEXT("Driving remains inside arena boundary"), Arena->ContainsCarLocation(Car->GetActorLocation(), Car->Hull->GetScaledBoxExtent().Size2D()));
    auto* BlockedExit = Box(Car->GetActorLocation() + FVector(0,0,100), FVector(600,600,300));
    Car->RequestExit();
    TestTrue(TEXT("Exit while driving begins controlled return"), Operation->State == ECarnivalOperationState::Returning);
    for (int32 I=0; I<180; ++I) Tick();
    TestTrue(TEXT("Blocked unloading retains protected passenger"), Player->RidePassenger->IsRiding() && Controller->GetPawn() == Car);
    BlockedExit->Destroy();
    for (int32 I=0; I<60; ++I) Tick();
    TestTrue(TEXT("Unloading restores player possession"), Controller->GetPawn() == Player);
    TestTrue(TEXT("Unloading restores collision and clears ride"), Player->GetActorEnableCollision() && !Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Cycle returns to loading"), Operation->State == ECarnivalOperationState::Loading);
    Player->SetActorLocation(Operation->Attendant->GetActorLocation(), false, nullptr, ETeleportType::TeleportPhysics);
    TestTrue(TEXT("Visitor can take operator control"), Operation->TakeOperatorControl(Player));
    TestTrue(TEXT("Operator starts driving session"), Operation->OperatorStart(Player));
    for (int32 I=0; I<20; ++I) Tick();
    TestTrue(TEXT("Operator can request stop"), Operation->OperatorStop(Player));
    Operation->ReleaseOperatorControl(Player);
    for (int32 I=0; I<60; ++I) Tick();
    TestTrue(TEXT("Attendant resumes ownership after handover"), !Operation->PlayerOperator && Operation->State == ECarnivalOperationState::Loading);
    // Destruction recovery uses the same real seat and controller, at a supported bay.
    Car->SetActorLocationAndRotation(FVector(0,0,36), FRotator::ZeroRotator, false, nullptr, ETeleportType::TeleportPhysics);
    Player->SetActorLocation(FVector(-300,0,98));
    if (TestTrue(TEXT("Next cycle can board again"), Operation->RequestBoard(Player)))
    {
        Car->Destroy();
        TestTrue(TEXT("Destroyed car restores possession"), Controller->GetPawn() == Player);
        TestTrue(TEXT("Destroyed car clears passenger state"), !Player->RidePassenger->IsRiding() && Player->GetActorEnableCollision());
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalPassengerScaleTest, "Carnival.Rides.PassengerScalePreservation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalPassengerScaleTest::RunTest(const FString&)
{
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("PassengerScale"));
    UWorld* World = Instance->GetWorld();
    const FURL URL;
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Ride = World->SpawnActor<AActor>();
    auto* Seat = NewObject<UCarnivalRideSeatComponent>(Ride);
    Ride->SetRootComponent(Seat); Seat->RegisterComponent(); Ride->SetActorScale3D(FVector(2,3,4));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>();
    const FVector PlayerScale(1.25f);
    Player->SetActorScale3D(PlayerScale);
    if (!TestTrue(TEXT("Scaled ride accepts passenger"), Player->RidePassenger->BoardRide(Ride, Seat))) return false;
    TestTrue(TEXT("Boarding preserves character size under nonuniformly scaled ride"), Player->GetActorScale3D().Equals(PlayerScale));
    Ride->SetActorScale3D(FVector(3,4,5));
    ++GFrameCounter; World->Tick(LEVELTICK_All, .016f);
    TestTrue(TEXT("Seat tracking preserves original character scale"), Player->GetActorScale3D().Equals(PlayerScale));
    Player->RidePassenger->UnboardRide(Player->RidePassenger->GetBoardingTransform());
    TestTrue(TEXT("Unloading retains character scale"), Player->GetActorScale3D().Equals(PlayerScale));
    return true;
}
#endif
