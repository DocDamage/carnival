#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalSaveSubsystem.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalMissionInteractionActor.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalSaveRoundTripTest, "Carnival.Save.SlotsAndSafeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCarnivalSaveRoundTripTest::RunTest(const FString&)
{
	auto* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("SaveSlots"));
	UWorld* World = Instance->GetWorld();
	auto* Saves = Instance->GetSubsystem<UCarnivalSaveSubsystem>();
	Saves->SlotPrefix = TEXT("Carnival_Automation_") + FGuid::NewGuid().ToString(EGuidFormats::Digits) + TEXT("_");
	ON_SCOPE_EXIT
	{
		for (int32 Slot = 1; Slot <= 3; ++Slot) for (int32 Bank = 0; Bank < 2; ++Bank)
			UGameplayStatics::DeleteGameInSlot(FString::Printf(TEXT("%s%d_%d"), *Saves->SlotPrefix, Slot, Bank), 0);
		World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World);
	};
	FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
	auto* Ground = World->SpawnActor<AActor>();
	auto* Floor = NewObject<UBoxComponent>(Ground);
	Ground->SetRootComponent(Floor); Floor->SetBoxExtent(FVector(5000, 5000, 20));
	Floor->SetCollisionProfileName(TEXT("BlockAll")); Floor->RegisterComponent(); Ground->SetActorLocation(FVector(0, 0, -20));
	FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0, 0, 100), FRotator::ZeroRotator, Params);
	auto* PC = World->SpawnActor<ACarnivalPlayerController>();
	PC->Possess(Player); PC->InitInputSystem(); Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	const FVector First(0, 0, Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2.f);
	Player->SetActorLocation(First);
	PC->SetControlRotation(FRotator(-20, 30, 0));
	auto* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>();
	auto* Campaign = Instance->GetSubsystem<UCarnivalCampaignSubsystem>();
	TestTrue(TEXT("Acquire inventory before saving"), Campaign->GrantSupply(TEXT("Timber"), 7));
	Mission->BeginStoryMission(); Mission->ReportMansionArrival(); Mission->CollectFoyerGlove(); Mission->CollectStudyLogAndKey();
	// Native door leaves use the production names; location is outside the player's fixture.
	auto* DoorActor = World->SpawnActor<AActor>();
	auto* DoorRoot = NewObject<USceneComponent>(DoorActor); DoorActor->SetRootComponent(DoorRoot); DoorRoot->RegisterComponent();
	for (const FName Name : { FName(TEXT("SM_Door02_D")), FName(TEXT("SM_Door02_E")) })
	{
		auto* Leaf = NewObject<UStaticMeshComponent>(DoorActor, Name); Leaf->SetupAttachment(DoorRoot); Leaf->RegisterComponent();
	}
	auto* Door = World->SpawnActor<ACarnivalMissionInteractionActor>();
	Door->Interaction = ECarnivalMissionInteraction::MusicRoomDoor; Door->ControlledDoorActor = DoorActor;
	TestTrue(TEXT("Open saved music-room door"), Door->RestoreSavedDoor(true));
	auto* Clue = World->SpawnActor<ACarnivalMissionInteractionActor>(); Clue->Interaction = ECarnivalMissionInteraction::FoyerGlove;
	auto* Build = Player->BuildComponent;
	Build->Categories.SetNum(1); Build->Categories[0].Pieces.Add(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
	TArray<FCarnivalSavedBuilding> Pieces;
	auto& Piece = Pieces.AddDefaulted_GetRef(); Piece.Mesh = FSoftObjectPath(Build->Categories[0].Pieces[0]);
	Piece.Transform = FTransform(FRotator::ZeroRotator, FVector(1000, 0, 52));
	FString Error;
	TestTrue(TEXT("Restore supported construction fixture"), Build->RestoreBuildings(Pieces, First, Error));
	TestTrue(TEXT("Slot one saves story, camera and construction"), Saves->SaveSlot(0, Player));
	Campaign->SpendSupply(TEXT("Timber"), 3);
	AddInfo(Saves->LastResult);
	Mission->ReportWorkerFound(); Player->SetActorLocation(First + FVector(500, 0, 0));
	Door->RestoreSavedDoor(false);
	TestTrue(TEXT("Slot two saves independently"), Saves->SaveSlot(1, Player));
	TestTrue(TEXT("Empty slot refuses load"), !Saves->LoadSlot(2, Player));
	TestTrue(TEXT("Third slot can be written independently"), Saves->SaveSlot(2, Player));
	TestTrue(TEXT("Load slot one"), Saves->LoadSlot(0, Player));
	AddInfo(Saves->LastResult);
	TestEqual(TEXT("Story returns to worker objective"), Mission->GetMissionState(), ECarnivalStoryMissionState::FindWorker);
	TestEqual(TEXT("Slot one restores inventory"), Campaign->GetItemCount(TEXT("Timber")), 7);
	TestTrue(TEXT("Player location restored"), Player->GetActorLocation().Equals(First));
	TestTrue(TEXT("Service key restored"), Mission->CanOpenMusicRoomDoor());
	TestFalse(TEXT("Later worker flag cleared"), Mission->bFoundWorker);
	TestTrue(TEXT("Saved open door is restored"), Door->IsSavedDoorOpen());
	TestTrue(TEXT("Consumed clue stays hidden after restore notification"), Clue->PropVisual->bHiddenInGame);
	TestEqual(TEXT("Construction replaced rather than duplicated"), Build->CaptureBuildings().Num(), 1);
	TestTrue(TEXT("Camera restored"), PC->GetControlRotation().Equals(FRotator(-20, 30, 0)));
	TestTrue(TEXT("Slot two retains separate progress"), Saves->LoadSlot(1, Player));
	TestEqual(TEXT("Second slot keeps its separate inventory"), Campaign->GetItemCount(TEXT("Timber")), 4);
	TestEqual(TEXT("Second slot worker progress"), Mission->GetMissionState(), ECarnivalStoryMissionState::RecoverMusicBox);
	TestFalse(TEXT("Second slot retains closed door state"), Door->IsSavedDoorOpen());
	TestTrue(TEXT("Save a second generation"), Saves->SaveSlot(0, Player));
	const FString NewBank = Saves->SlotPrefix + TEXT("1_1");
	// Simulate a structurally incompatible newest generation. Older bank must remain usable.
	auto* Incompatible = NewObject<UCarnivalSaveGame>(); Incompatible->Version = 999;
	UGameplayStatics::SaveGameToSlot(Incompatible, NewBank, 0);
	TestTrue(TEXT("Older bank recovers from incompatible newest write"), Saves->LoadSlot(0, Player));
	TestEqual(TEXT("Recovered bank has original objective"), Mission->GetMissionState(), ECarnivalStoryMissionState::FindWorker);
	TestFalse(TEXT("Negative slots are rejected"), Saves->SaveSlot(-1, Player));
	TestFalse(TEXT("Out of range slots are rejected"), Saves->LoadSlot(3, Player));
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	TestFalse(TEXT("Mid-fall save is rejected"), Saves->SaveSlot(0, Player));
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	Mission->ReportWorkerFound(); Mission->RecoverMusicBox();
	TestFalse(TEXT("Scare playback cannot be saved"), Saves->SaveSlot(0, Player));
	TestFalse(TEXT("Invalid stage cannot be restored"), Mission->RestoreSavedState(static_cast<ECarnivalStoryMissionState>(255)));
	Mission->ReportDollScareComplete();
	Player->SetActorLocation(First + FVector(500, 0, 0));
	// Restore validation must not alter progress, location, or buildings on obstruction.
	auto* Blocker = World->SpawnActor<AActor>(); auto* Box = NewObject<UBoxComponent>(Blocker);
	Blocker->SetRootComponent(Box); Box->SetBoxExtent(FVector(60, 60, 100)); Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent(); Blocker->SetActorLocation(First);
	const FVector Before = Player->GetActorLocation();
	TestFalse(TEXT("Blocked saved player position rejects load"), Saves->LoadSlot(0, Player));
	TestTrue(TEXT("Rejected load keeps player"), Player->GetActorLocation().Equals(Before));
	TestEqual(TEXT("Rejected load keeps mission"), Mission->GetMissionState(), ECarnivalStoryMissionState::EscapeMansion);
	TestEqual(TEXT("Rejected load keeps construction"), Build->CaptureBuildings().Num(), 1);
	Blocker->Destroy();
	const FString LegacyBank = Saves->SlotPrefix + TEXT("1_0");
	auto* Legacy = Cast<UCarnivalSaveGame>(UGameplayStatics::LoadGameFromSlot(LegacyBank, 0));
	Legacy->Version = 1; Legacy->MissionState = ECarnivalStoryMissionState::Complete; Legacy->Campaign = FCarnivalCampaignSnapshot();
	TestTrue(TEXT("Write isolated legacy version-one fixture"), UGameplayStatics::SaveGameToSlot(Legacy, LegacyBank, 0));
	TestTrue(TEXT("Load legacy version-one story without losing its position/buildings"), Saves->LoadSlot(0, Player));
	TestTrue(TEXT("Legacy completed story unlocks sequel"), Campaign->CanUseStation(TEXT("hospital_reception")));
	TestEqual(TEXT("Legacy save begins with empty new inventory"), Campaign->Capture().Inventory.Num(), 0);
	TestTrue(TEXT("Start sequel after legacy migration"), Campaign->UseStation(TEXT("hospital_reception"), 0));
	Campaign->GrantSupply(TEXT("Timber"), 9);
	TestTrue(TEXT("Save sequel and inventory in independent slot"), Saves->SaveSlot(2, Player));
	Campaign->UseStation(TEXT("hospital_ward"), 0); Campaign->SpendSupply(TEXT("Timber"), 5);
	Player->SetActorLocation(First + FVector(500, 0, 0));
	auto* CampaignBlocker = World->SpawnActor<AActor>(); auto* CampaignBox = NewObject<UBoxComponent>(CampaignBlocker);
	CampaignBlocker->SetRootComponent(CampaignBox); CampaignBox->SetBoxExtent(FVector(60, 60, 100));
	CampaignBox->SetCollisionProfileName(TEXT("BlockAll")); CampaignBox->RegisterComponent(); CampaignBlocker->SetActorLocation(First);
	TestFalse(TEXT("Blocked sequel restore is rejected"), Saves->LoadSlot(2, Player));
	TestEqual(TEXT("Rejected load keeps sequel progress"), Campaign->Capture().CompletedStations, 2);
	TestEqual(TEXT("Rejected load keeps current supplies"), Campaign->GetItemCount(TEXT("Timber")), 4);
	CampaignBlocker->Destroy();
	TestTrue(TEXT("Clear sequel restore succeeds"), Saves->LoadSlot(2, Player));
	TestEqual(TEXT("Sequel stage restores from slot"), Campaign->Capture().CompletedStations, 1);
	TestEqual(TEXT("Sequel quest item restores without duplication"), Campaign->GetItemCount(TEXT("VisitingPass")), 1);
	TestEqual(TEXT("Sequel supplies restore from slot"), Campaign->GetItemCount(TEXT("Timber")), 9);
	auto* Version2 = Cast<UCarnivalSaveGame>(UGameplayStatics::LoadGameFromSlot(LegacyBank, 0));
	Version2->Version = 2; Version2->Campaign = FCarnivalCampaignSnapshot(); Version2->Campaign.bUnlocked = true;
	Version2->Campaign.CompletedStations = 8; Version2->Campaign.Inventory.Add({FName(TEXT("ClockSeal")), 1});
	TestTrue(TEXT("Write isolated version-two fixture past a removed station"), UGameplayStatics::SaveGameToSlot(Version2, LegacyBank, 0));
	TestTrue(TEXT("Load version-two campaign slot"), Saves->LoadSlot(0, Player));
	TestEqual(TEXT("Version-two progress maps to the current chain"), Campaign->Capture().CompletedStations, 6);
	TestTrue(TEXT("Removed-station token becomes the next expected item"),
		Campaign->GetItemCount(TEXT("RepairLedger")) == 1 && Campaign->GetItemCount(TEXT("ClockSeal")) == 0);
	TestTrue(TEXT("Migrated slot continues at the prison"), Campaign->CanUseStation(TEXT("prison_archive")));
	Pieces[0].Mesh = FSoftObjectPath(TEXT("/Game/Unavailable.Unavailable"));
	TestFalse(TEXT("Missing build piece is rejected transactionally"), Build->RestoreBuildings(Pieces, Before, Error));
	TestEqual(TEXT("Rejected construction restore keeps prior pieces"), Build->CaptureBuildings().Num(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalSessionMenuTest, "Carnival.Input.SessionMenuNavigation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCarnivalSessionMenuTest::RunTest(const FString&)
{
	auto* Instance = NewObject<UGameInstance>(GEngine); Instance->InitializeStandalone(TEXT("SessionMenu"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase")); World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
	auto* PC = World->SpawnActor<ACarnivalPlayerController>(); PC->InitInputSystem();
	auto Press = [&](FKey Key, EInputEvent Event = IE_Pressed) { PC->InputKey(FInputKeyEventArgs::CreateSimulated(Key, Event, 1.f)); };
	Press(EKeys::Gamepad_Special_Right);
	TestTrue(TEXT("Options pauses and opens menu"), PC->bSessionMenuOpen && World->IsPaused());
	Press(EKeys::Gamepad_DPad_Up);
	TestEqual(TEXT("Up from Resume wraps to Return to path"), PC->SessionMenuSelection, 9);
	Press(EKeys::Gamepad_FaceButton_Bottom);
	TestEqual(TEXT("Return to path asks for confirmation"), PC->SessionMenuConfirmation, 9);
	Press(EKeys::Gamepad_FaceButton_Right);
	Press(EKeys::Gamepad_DPad_Down);
	TestEqual(TEXT("Down from Return to path wraps to Resume"), PC->SessionMenuSelection, 0);
	Press(EKeys::Gamepad_DPad_Down); Press(EKeys::Gamepad_DPad_Left);
	TestEqual(TEXT("Left wraps all three slots"), PC->SelectedSaveSlot, 2);
	Press(EKeys::Gamepad_DPad_Down); Press(EKeys::Gamepad_FaceButton_Bottom);
	TestEqual(TEXT("Save asks for reviewable overwrite confirmation"), PC->SessionMenuConfirmation, 2);
	Press(EKeys::Gamepad_FaceButton_Bottom, IE_Repeat);
	TestEqual(TEXT("Held confirm cannot overwrite a slot"), PC->SessionMenuConfirmation, 2);
	Press(EKeys::Gamepad_FaceButton_Right);
	TestEqual(TEXT("Circle cancels confirmation"), PC->SessionMenuConfirmation, -1);
	TestTrue(TEXT("Cancel leaves menu paused"), PC->bSessionMenuOpen && World->IsPaused());
	PC->SessionMenuSelection = 5; Press(EKeys::Gamepad_FaceButton_Bottom);
	TestTrue(TEXT("Settings opens from pause"), PC->bSettingsMenuOpen && !PC->bSessionMenuOpen && World->IsPaused());
	Press(EKeys::Gamepad_FaceButton_Right);
	TestTrue(TEXT("Settings returns to pause without unpausing"), !PC->bSettingsMenuOpen && PC->bSessionMenuOpen && World->IsPaused());
	PC->SessionMenuSelection = 7; Press(EKeys::Gamepad_FaceButton_Bottom);
	TestTrue(TEXT("Controller opens inventory while paused"), PC->bSessionRecordsOpen && !PC->bJournalTab && World->IsPaused());
	Press(EKeys::Gamepad_DPad_Right);
	TestTrue(TEXT("Controller switches to journal"), PC->bJournalTab);
	Press(EKeys::Gamepad_DPad_Down); TestEqual(TEXT("Controller pages through records"), PC->RecordsPage, 1);
	Press(EKeys::Gamepad_FaceButton_Right); TestFalse(TEXT("Circle returns to pause menu"), PC->bSessionRecordsOpen);
	Press(EKeys::Escape);
	TestFalse(TEXT("Keyboard Escape resumes"), PC->bSessionMenuOpen || World->IsPaused());
	return true;
}
#endif
