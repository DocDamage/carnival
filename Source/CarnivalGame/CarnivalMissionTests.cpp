#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalMissionSubsystem.h"
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalMissionStateFlowTest, "Carnival.StoryMission.StateFlow",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalMissionStateFlowTest::RunTest(const FString&)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("CarnivalMissionStateFlow"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };

	UCarnivalMissionSubsystem* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>();
	if (!TestNotNull(TEXT("Game instance creates the story mission subsystem"), Mission)) return false;
	FActorSpawnParameters BikeSpawn;
	BikeSpawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FTransform BikeStart(FRotator(0.f, 35.f, 0.f), FVector(450.f, 120.f, 100.f));
	ACarnivalMotorcycle* Bike = World->SpawnActor<ACarnivalMotorcycle>(ACarnivalMotorcycle::StaticClass(), BikeStart, BikeSpawn);
	if (!TestNotNull(TEXT("Retry test creates a placed motorcycle"), Bike)) return false;

	TestEqual(TEXT("Story begins in free play"), Mission->GetMissionState(), ECarnivalStoryMissionState::FreePlay);
	TestFalse(TEXT("Mansion arrival cannot skip story start"), Mission->ReportMansionArrival());
	TestFalse(TEXT("Locked music-room door stays locked without the key"), Mission->CanOpenMusicRoomDoor());
	TestTrue(TEXT("Notice board starts the story"), Mission->BeginStoryMission());
	TestEqual(TEXT("Story starts with the mansion objective"), Mission->GetMissionState(), ECarnivalStoryMissionState::FindMansion);
	TestFalse(TEXT("Music box cannot be recovered before finding the worker"), Mission->RecoverMusicBox());
	TestTrue(TEXT("Mansion arrival starts foyer search"), Mission->ReportMansionArrival());
	TestTrue(TEXT("Foyer glove advances to the study"), Mission->CollectFoyerGlove());
	TestFalse(TEXT("Foyer clue cannot be collected twice"), Mission->CollectFoyerGlove());
	TestTrue(TEXT("Study log grants the service key"), Mission->CollectStudyLogAndKey());
	TestFalse(TEXT("Service key cannot be collected twice"), Mission->CollectStudyLogAndKey());
	TestTrue(TEXT("Service key opens the music-room door"), Mission->CanOpenMusicRoomDoor());
	TestTrue(TEXT("Finding the worker advances the box objective"), Mission->ReportWorkerFound());
	TestFalse(TEXT("Worker interaction cannot advance twice"), Mission->ReportWorkerFound());
	TestTrue(TEXT("Music box can be recovered after the worker"), Mission->RecoverMusicBox());
	TestFalse(TEXT("Music box cannot be recovered twice"), Mission->RecoverMusicBox());
	TestTrue(TEXT("Doll encounter completes without a failure branch"), Mission->ReportDollScareComplete());
	TestFalse(TEXT("Story cannot finish before leaving the mansion"), Mission->ReportCarnivalReturned());
	TestTrue(TEXT("Leaving the mansion starts the return"), Mission->ReportMansionEscaped());
	TestTrue(TEXT("Returning to Carnival completes the story"), Mission->ReportCarnivalReturned());
	TestTrue(TEXT("Completion returns to free play"), Mission->IsMissionComplete() && !Mission->IsMissionActive());
	TestEqual(TEXT("Completion notice clearly states the outcome"), Mission->GetCurrentObjective(),
		FText::FromString(TEXT("Worker found. Music box recovered. Carnival free play is open.")));
	TestFalse(TEXT("Carnival return cannot complete the story twice"), Mission->ReportCarnivalReturned());
	TestTrue(TEXT("Completed mission can be replayed from the notice board"), Mission->BeginStoryMission());
	TestEqual(TEXT("Board replay returns to the mansion objective"), Mission->GetMissionState(), ECarnivalStoryMissionState::FindMansion);
	TestFalse(TEXT("Board replay clears the carried key"), Mission->CanOpenMusicRoomDoor());
	TestFalse(TEXT("Board replay clears the worker flag"), Mission->bFoundWorker);
	TestFalse(TEXT("Board replay clears the music box flag"), Mission->bRecoveredMusicBox);
	TestTrue(TEXT("A live mission can be retried"), Mission->ReportMansionArrival());
	TestTrue(TEXT("Retry can clear partial clue progress"), Mission->CollectFoyerGlove());
	Bike->SetActorLocation(FVector(-300.f, 900.f, 260.f));
	Bike->CurrentSpeed = 640.f;
	Bike->Destroy();
	TestTrue(TEXT("Retry restarts the mansion objective"), Mission->RetryStoryMission());
	ACarnivalMotorcycle* RestoredBike = nullptr;
	for (TActorIterator<ACarnivalMotorcycle> It(World); It; ++It)
	{
		if (IsValid(*It))
		{
			RestoredBike = *It;
			break;
		}
	}
	if (!TestNotNull(TEXT("Retry restores a destroyed placed motorcycle"), RestoredBike)) return false;
	TestTrue(TEXT("Retry restores the motorcycle start position and heading"),
		RestoredBike->GetActorTransform().Equals(BikeStart, .1f));
	TestEqual(TEXT("Retry clears motorcycle speed"), RestoredBike->CurrentSpeed, 0.f);
	TestFalse(TEXT("Replay clears the carried key"), Mission->CanOpenMusicRoomDoor());
	TestFalse(TEXT("Retry clears the foyer clue"), Mission->bFoundFoyerGlove);
	TestFalse(TEXT("Replay clears the worker flag"), Mission->bFoundWorker);
	TestFalse(TEXT("Replay clears the music box flag"), Mission->bRecoveredMusicBox);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalMissionDoorInteractionTest, "Carnival.StoryMission.DoorInteraction",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalMissionDoorInteractionTest::RunTest(const FString&)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("CarnivalMissionDoorInteraction"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL);
	World->InitializeActorsForPlay(URL);

	FActorSpawnParameters Spawn;
	Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	UClass* DoorClass = LoadClass<AActor>(nullptr, TEXT("/Game/Mansion/Mesh/Assets/Doors/BP_Door02.BP_Door02_C"));
	if (!TestNotNull(TEXT("Authored mansion door Blueprint loads"), DoorClass)) return false;
	AActor* Door = World->SpawnActor<AActor>(DoorClass, FVector(120.f, 0.f, 0.f), FRotator::ZeroRotator, Spawn);
	UStaticMeshComponent* LeftLeaf = nullptr;
	UStaticMeshComponent* RightLeaf = nullptr;
	TArray<UStaticMeshComponent*> DoorMeshes;
	Door->GetComponents<UStaticMeshComponent>(DoorMeshes);
	for (UStaticMeshComponent* Mesh : DoorMeshes)
	{
		if (Mesh->GetName() == TEXT("SM_Door02_D")) LeftLeaf = Mesh;
		if (Mesh->GetName() == TEXT("SM_Door02_E")) RightLeaf = Mesh;
	}
	if (!TestNotNull(TEXT("Authored door has the expected left leaf"), LeftLeaf)
		|| !TestNotNull(TEXT("Authored door has the expected right leaf"), RightLeaf)) return false;
	const float ClosedLeftYaw = LeftLeaf->GetRelativeRotation().Yaw;
	const float ClosedRightYaw = RightLeaf->GetRelativeRotation().Yaw;

	ACarnivalPlayerCharacter* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
	ACarnivalMissionInteractionActor* MissionDoor = World->SpawnActor<ACarnivalMissionInteractionActor>(FVector(40.f, 0.f, 0.f), FRotator::ZeroRotator, Spawn);
	MissionDoor->Interaction = ECarnivalMissionInteraction::MusicRoomDoor;
	MissionDoor->ControlledDoorActor = Door;
	ACarnivalMissionInteractionActor* MansionEntrance = World->SpawnActor<ACarnivalMissionInteractionActor>(FVector(40.f, 200.f, 0.f), FRotator::ZeroRotator, Spawn);
	MansionEntrance->Interaction = ECarnivalMissionInteraction::MansionEntrance;
	ACarnivalMissionInteractionActor* MansionExit = World->SpawnActor<ACarnivalMissionInteractionActor>(FVector(80.f, 200.f, 0.f), FRotator::ZeroRotator, Spawn);
	MansionExit->Interaction = ECarnivalMissionInteraction::MansionExit;
	ACarnivalMissionInteractionActor* CarnivalReturn = World->SpawnActor<ACarnivalMissionInteractionActor>(FVector(120.f, 300.f, 0.f), FRotator::ZeroRotator, Spawn);
	CarnivalReturn->Interaction = ECarnivalMissionInteraction::CarnivalReturn;
	ACarnivalPlayerCharacter* SightPlayer = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0.f, 200.f, 0.f), FRotator::ZeroRotator, Spawn);
	AActor* ClosedDoorSightBlocker = World->SpawnActor<AActor>(FVector(60.f, 200.f, 0.f), FRotator::ZeroRotator, Spawn);
	UBoxComponent* SightBlockerBox = NewObject<UBoxComponent>(ClosedDoorSightBlocker);
	ClosedDoorSightBlocker->SetRootComponent(SightBlockerBox);
	SightBlockerBox->SetBoxExtent(FVector(10.f, 100.f, 100.f));
	SightBlockerBox->SetCollisionProfileName(TEXT("BlockAll"));
	SightBlockerBox->RegisterComponent();
	SightBlockerBox->SetWorldLocation(FVector(60.f, 200.f, 0.f));
	ACarnivalMissionInteractionActor* SightMissionDoor = World->SpawnActor<ACarnivalMissionInteractionActor>(FVector(120.f, 200.f, 0.f), FRotator::ZeroRotator, Spawn);
	SightMissionDoor->Interaction = ECarnivalMissionInteraction::MusicRoomDoor;
	SightMissionDoor->InteractionRadius = 125.f;
	SightMissionDoor->ControlledDoorActor = ClosedDoorSightBlocker;
	World->BeginPlay();
	TestEqual(TEXT("Mansion entrance has a clear foot-only prompt"), MansionEntrance->GetPromptText().ToString(), FString(TEXT("Enter the mansion on foot")));
	TestEqual(TEXT("Mansion exit has a clear prompt"), MansionExit->GetPromptText().ToString(), FString(TEXT("Leave the mansion")));
	TestEqual(TEXT("Carnival return has a clear prompt"), CarnivalReturn->GetPromptText().ToString(), FString(TEXT("Return to the Carnival")));

	UCarnivalMissionSubsystem* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>();
	TestTrue(TEXT("Test mission starts"), Mission->BeginStoryMission());
	TestTrue(TEXT("Player reports reaching the mansion"), Mission->ReportMansionArrival());
	TestTrue(TEXT("Closed music-room leaf does not hide its nearby interaction prompt"), SightMissionDoor->CanInteract(SightPlayer));
	TestTrue(TEXT("Mission door can be focused while it is locked"), MissionDoor->CanInteract(Player));
	TestFalse(TEXT("Locked mission door rejects use without the key"), MissionDoor->TryInteract(Player));
	TestTrue(TEXT("A locked attempt leaves both door leaves closed"),
		FMath::IsNearlyEqual(LeftLeaf->GetRelativeRotation().Yaw, ClosedLeftYaw, .1f)
		&& FMath::IsNearlyEqual(RightLeaf->GetRelativeRotation().Yaw, ClosedRightYaw, .1f));

	TestTrue(TEXT("Foyer clue advances to the study"), Mission->CollectFoyerGlove());
	TestTrue(TEXT("Study key unlocks the music room"), Mission->CollectStudyLogAndKey());
	TestTrue(TEXT("Keyed mission door accepts interaction"), MissionDoor->TryInteract(Player));
	MissionDoor->Tick(.6f);
	TestTrue(TEXT("Door interaction animates both authored leaves open"),
		FMath::IsNearlyEqual(FRotator::NormalizeAxis(LeftLeaf->GetRelativeRotation().Yaw - ClosedLeftYaw), 90.f, 1.f)
		&& FMath::IsNearlyEqual(FRotator::NormalizeAxis(RightLeaf->GetRelativeRotation().Yaw - ClosedRightYaw), -90.f, 1.f));

	TestTrue(TEXT("Retry resets the mission"), Mission->RetryStoryMission());
	TestTrue(TEXT("Retry closes the mission door leaves"),
		FMath::IsNearlyEqual(LeftLeaf->GetRelativeRotation().Yaw, ClosedLeftYaw, .1f)
		&& FMath::IsNearlyEqual(RightLeaf->GetRelativeRotation().Yaw, ClosedRightYaw, .1f));
	return true;
}

#endif
