#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalRideBlockedUnloadTest, "Carnival.Rides.BlockedUnloading",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalRideBlockedUnloadTest::RunTest(const FString&)
{
    UClass* RideClass = LoadClass<AActor>(nullptr, TEXT("/Game/Carnival/Rides/BP_Swing_Carnival.BP_Swing_Carnival_C"));
    if (!TestNotNull(TEXT("Real swing asset loads"), RideClass)) return false;
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("BlockedRideUnload"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto MakeBlock = [&](FVector Position, FVector Extent)
    {
        auto* Actor = World->SpawnActor<AActor>();
        auto* Box = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Box); Box->SetBoxExtent(Extent);
        Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent();
        Actor->SetActorLocation(Position);
        return Actor;
    };
    auto* Floor = MakeBlock(FVector(0,0,-20), FVector(5000,5000,20));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Ride = World->SpawnActor<AActor>(RideClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    auto* Staff = World->SpawnActor<ACarnivalRideAttendant>(FVector(2200,0,91), FRotator::ZeroRotator, Spawn);
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(2400,0,98), FRotator::ZeroRotator, Spawn);
    Player->GetCharacterMovement()->bRunPhysicsWithNoController = true;
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    if (!TestTrue(TEXT("Staff assignment succeeds"), Staff->AssignRide(Ride))) return false;
    auto* Operation = Staff->Operation.Get();
    Operation->BoardingSeconds=.1f; Operation->SecuringSeconds=.1f;
    Operation->CycleSeconds=1.f; Operation->ReturnSeconds=.5f; Operation->UnloadingSeconds=.1f;
    auto Step = [&](float Seconds)
    {
        for (int32 I=0; I<FMath::CeilToInt(Seconds*60); ++I)
        { ++GFrameCounter; World->Tick(LEVELTICK_All,1.f/60.f); }
    };
    Step(.2f);
    const FTransform Entry = Player->GetActorTransform();
    if (!TestTrue(TEXT("Player boards before obstacle arrives"), Operation->RequestBoard(Player))) return false;
    auto* Seat = Player->RidePassenger->GetCurrentSeat();
    auto* Blocker = MakeBlock(Entry.GetLocation(), FVector(80,80,160));
    Step(2.2f);
    TestEqual(TEXT("Blocked ground exit retains unloading state"), Operation->State, ECarnivalOperationState::Unloading);
    TestTrue(TEXT("Player stays seated with movement disabled"), Player->RidePassenger->IsRiding()
        && Player->GetCharacterMovement()->MovementMode==MOVE_None);
    TestTrue(TEXT("Seat ownership remains intact while exit blocked"), Seat->GetOccupant()==Player);
    TestFalse(TEXT("Blocked exit does not re-enable player collision"), Player->GetActorEnableCollision());
    TestFalse(TEXT("Blocked unloading cannot start another cycle"), Operation->OperatorStart(Player));
    Blocker->Destroy();
    Step(.2f);
    TestFalse(TEXT("Clearing exit automatically releases passenger"), Player->RidePassenger->IsRiding());
    TestEqual(TEXT("Cleared exit reopens staffed ride"), Operation->State, ECarnivalOperationState::Loading);
    TestTrue(TEXT("Passenger returns to original ground position"), Player->GetActorLocation().Equals(Entry.GetLocation(),5.f));
    TestTrue(TEXT("Collision is restored after verified exit"), Player->GetActorEnableCollision());

    if (!TestTrue(TEXT("Second passenger cycle boards"), Operation->RequestBoard(Player))) return false;
    Floor->SetActorEnableCollision(false);
    Staff->Destroy();
    Step(.4f);
    TestEqual(TEXT("Attendant loss with missing floor waits for safe unloading"), Operation->State, ECarnivalOperationState::Unloading);
    TestTrue(TEXT("Walking passenger is not released over missing support"), Player->RidePassenger->IsRiding());
    Floor->SetActorEnableCollision(true);
    Step(.2f);
    TestFalse(TEXT("Restored floor permits release without attendant"), Player->RidePassenger->IsRiding());
    TestEqual(TEXT("Ride closes only after passenger release"), Operation->State, ECarnivalOperationState::Closed);
    return true;
}
#endif
