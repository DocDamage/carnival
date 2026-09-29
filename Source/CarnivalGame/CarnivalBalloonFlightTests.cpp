#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalBalloonFlightComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRideControllerComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/OverlapResult.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalBalloonFlightTest, "Carnival.Rides.BalloonGroundStation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalBalloonFlightTest::RunTest(const FString&)
{
    UClass* RideClass=LoadClass<AActor>(nullptr,TEXT("/Game/Carnival/Rides/BP_HotAirBalloon_Carnival.BP_HotAirBalloon_Carnival_C"));
    if (!TestNotNull(TEXT("Project balloon asset loads"),RideClass)) return false;
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("BalloonGroundStation"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto MakeBlock=[&](FVector Position,FVector Extent)
    {
        AActor* Actor=World->SpawnActor<AActor>();
        auto* Box=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Box); Box->SetBoxExtent(Extent);
        Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent();
        Actor->SetActorLocation(Position);
        return Actor;
    };
    MakeBlock(FVector(0,0,-25),FVector(6000,6000,25));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Ride=World->SpawnActor<AActor>(RideClass,FVector(0,0,672.1),FRotator::ZeroRotator,Spawn);
    UStaticMeshComponent* Mesh=nullptr;
    TArray<UStaticMeshComponent*> Meshes; Ride->GetComponents<UStaticMeshComponent>(Meshes);
    for (auto* Candidate:Meshes) if (Candidate->GetFName()==TEXT("StaticMeshComponent1")) Mesh=Candidate;
    if (!TestNotNull(TEXT("Measured balloon basket mesh exists"),Mesh)) return false;
    auto* Flight=Ride->FindComponentByClass<UCarnivalBalloonFlightComponent>();
    if (!Flight) { Flight=NewObject<UCarnivalBalloonFlightComponent>(Ride); Ride->AddInstanceComponent(Flight); Flight->RegisterComponent(); }
    Flight->FlightHeight=1200.f;
    auto* Controller=Ride->FindComponentByClass<UCarnivalRideControllerComponent>();
    if (!TestNotNull(TEXT("Balloon passenger controller exists"),Controller)) return false;
    Controller->RefreshSeats();
    if (Controller->GetSeats().IsEmpty())
    {
        auto* Seat=NewObject<UCarnivalRideSeatComponent>(Ride);
        Seat->SeatId=TEXT("MeasuredStandingBasket"); Seat->bStandingPassenger=true;
        Seat->SetupAttachment(Mesh); Seat->SetRelativeLocation(FVector(0,0,-646.1));
        Seat->PassengerOffset=FTransform(FVector(0,0,96)); Seat->RegisterComponent();
    }
    auto* Staff=World->SpawnActor<ACarnivalRideAttendant>(FVector(350,0,98),FRotator::ZeroRotator,Spawn);
    TestTrue(TEXT("Ground staff accepts balloon"),Staff->AssignRide(Ride));
    auto* Operation=Staff->Operation.Get();
    Operation->BoardingSeconds=.1f; Operation->SecuringSeconds=.1f;
    Operation->CycleSeconds=2.4f; Operation->ReturnSeconds=.5f; Operation->UnloadingSeconds=.1f;
    auto* Player=World->SpawnActor<ACarnivalPlayerCharacter>(FVector(600,0,120),FRotator::ZeroRotator,Spawn);
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Player);
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    Player->SetActorScale3D(FVector(1.15));
    auto Step=[&](float Seconds)
    {
        for (int32 I=0; I<FMath::CeilToInt(Seconds*60); ++I)
        { ++GFrameCounter; World->Tick(LEVELTICK_All,1.f/60.f); }
    };
    Step(.2f);
    if (!TestTrue(TEXT("Ground balloon opens after initialization"),Operation->IsReady())) return false;
    TestTrue(TEXT("Flight component resolves operation and mesh"),Flight->ConfigurationError.IsEmpty());
    // Character/controller startup can settle the initial spawn before scaling.
    // Place the final scaled capsule above the real floor before boarding.
    Player->SetActorLocation(FVector(600,0,Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+2.f),
        false,nullptr,ETeleportType::TeleportPhysics);
    Player->GetCharacterMovement()->StopMovementImmediately();
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    const FTransform Home=Mesh->GetComponentTransform();
    const FTransform Entry=Player->GetActorTransform();
    TestTrue(TEXT("Ground passenger boards"),Operation->RequestBoard(Player));
    auto* Seat=Player->RidePassenger->GetCurrentSeat();
    if (!TestNotNull(TEXT("Standing basket position assigned"),Seat)) return false;
    const FVector SeatHome=Seat->GetComponentLocation();
    Step(1.2f);
    TestEqual(TEXT("Flight reaches running state"),Operation->State,ECarnivalOperationState::Running);
    TestTrue(TEXT("Standing position rises with actual balloon"),Seat->GetComponentLocation().Z-SeatHome.Z>600.f);
    TestTrue(TEXT("Passenger remains attached during ascent"),Player->GetActorLocation().Equals(Seat->GetPassengerWorldTransform().GetLocation(),1.f));
    TestTrue(TEXT("Passenger world scale remains unchanged"),Player->GetActorScale3D().Equals(Entry.GetScale3D(),.001));
    TestTrue(TEXT("Balloon does not steal player controller"),PC->GetPawn()==Player);
    TestFalse(TEXT("Clear flight is not obstructed"),Flight->bLastCycleObstructed);
    Step(3.f);
    if (Player->RidePassenger->IsRiding())
    {
        float Radius, HalfHeight;
        Player->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
        TArray<FOverlapResult> Overlaps;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(BalloonUnloadFixture), false, Player);
        World->OverlapMultiByProfile(Overlaps, Entry.GetLocation(), Entry.GetRotation(), TEXT("Pawn"),
            FCollisionShape::MakeCapsule(Radius, HalfHeight), Query);
        AddInfo(FString::Printf(TEXT("Blocked balloon fixture entry=%s radius=%.2f halfheight=%.2f"), *Entry.GetLocation().ToString(), Radius, HalfHeight));
        for (const FOverlapResult& Overlap : Overlaps)
            AddInfo(FString::Printf(TEXT("Exit overlap actor=%s component=%s blocking=%d"),
                *GetNameSafe(Overlap.GetActor()), *GetNameSafe(Overlap.GetComponent()), Overlap.bBlockingHit));
    }
    TestEqual(TEXT("Natural cycle reopens ground boarding"),Operation->State,ECarnivalOperationState::Loading);
    TestFalse(TEXT("Natural return unloads passenger"),Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Natural return restores loading mesh pose"),Mesh->GetComponentTransform().Equals(Home,.1));
    TestTrue(TEXT("Natural unload restores player entry transform"),Player->GetActorTransform().Equals(Entry,.1));
    TestTrue(TEXT("Natural unload restores collision"),Player->GetActorEnableCollision());

    const double RoofZ=Home.TransformPosition(FVector(0,0,Mesh->GetStaticMesh()->GetBoundingBox().Max.Z)).Z;
    MakeBlock(FVector(0,0,RoofZ+600),FVector(2000,2000,20));
    TestTrue(TEXT("Second boarding starts obstructed-flight fixture"),Operation->RequestBoard(Player));
    for (int32 I=0; I<120 && !Flight->bLastCycleObstructed; ++I) Step(1.f/60.f);
    TestTrue(TEXT("Flight detects overhead obstruction"),Flight->bLastCycleObstructed);
    TestEqual(TEXT("Obstruction requests controlled platform return"),Operation->State,ECarnivalOperationState::Returning);
    TestTrue(TEXT("Passenger stays attached until return is complete"),Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Balloon stops below obstruction"),Flight->CurrentLift<600.f);
    Step(1.f);
    TestEqual(TEXT("Blocked cycle returns to staffed loading"),Operation->State,ECarnivalOperationState::Loading);
    TestFalse(TEXT("Blocked flight releases passenger at ground"),Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Blocked flight restores boarding transform and scale"),Player->GetActorTransform().Equals(Entry,.1));
    TestTrue(TEXT("Blocked flight restores player collision"),Player->GetActorEnableCollision());
    TestTrue(TEXT("Blocked flight retains player controller"),PC->GetPawn()==Player);
    TestEqual(TEXT("Original movement mode is restored"),Player->GetCharacterMovement()->MovementMode.GetValue(),MOVE_Flying);
    return true;
}
#endif
