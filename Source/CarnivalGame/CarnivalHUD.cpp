// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalHUD.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRideOperationComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalBumperCar.h"
#include "CarnivalBumperArenaComponent.h"
#include "CarnivalAudioSettingsSubsystem.h"
#include "CarnivalWeaponBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalActivityBase.h"
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalDoorSubsystem.h"
#include "CarnivalMissionSubsystem.h"
#include "CarnivalSaveSubsystem.h"
#include "CarnivalCampaignSubsystem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"

ACarnivalHUD::ACarnivalHUD()
{
	bShowHelpOverlay = false;
	bShowSettingsMenu = false;
}

void ACarnivalHUD::DrawHUD()
{
	Super::DrawHUD();

	if (!Canvas || !GEngine)
	{
		return;
	}

	ACarnivalPlayerController* PC = Cast<ACarnivalPlayerController>(GetOwningPlayerController());
	ACarnivalPlayerCharacter* Char = PC ? Cast<ACarnivalPlayerCharacter>(PC->GetPawn()) : nullptr;
	if (PC && PC->bControllerDisconnectPaused)
	{
		TArray<FString> Lines;
		Lines.Add(TEXT("Reconnect the controller, or press any key to continue."));
		Lines.Add(TEXT("Keyboard and controller input are both available."));
		const float Width = FMath::Min(640.f, Canvas->ClipX - 40.f);
		DrawBoxWithText((Canvas->ClipX - Width) * .5f, (Canvas->ClipY - 92.f) * .5f, Width, 92.f,
			TEXT("CONTROLLER DISCONNECTED"), Lines,
			FLinearColor(.015f,.02f,.03f,.96f), FLinearColor(1.f,.72f,.3f), FLinearColor::White);
		return;
	}
	if (PC && PC->bSessionMenuOpen)
	{
		DrawSessionMenu(PC);
		return;
	}
	if (PC && PC->bSettingsMenuOpen)
	{
		DrawSettingsMenu(PC);
		return;
	}

	DrawCrosshair();

	if (bShowHelpOverlay)
	{
		DrawTelemetry(Char, PC);
#if WITH_EDITOR
		DrawFastTravelGuide();
#endif
	}
	if (Char && Char->BuildComponent && Char->BuildComponent->bIsBuildModeActive)
	{
		DrawBuildModeHUD(Char);
		return;
	}

	DrawActivityOverlay(Char, PC);
	DrawVehicleControls(PC);
	DrawStoryMissionOverlay(PC);
	DrawStoryInteractionPrompt(Char, PC);
	DrawPlayerRecoveryPrompt(Char, PC);
	DrawRideInteraction(Char, PC);

}

void ACarnivalHUD::DrawVehicleControls(ACarnivalPlayerController* PC)
{
	if (!PC || !PC->GetPawn()) return;
	const auto* Bike = Cast<ACarnivalMotorcycle>(PC->GetPawn());
	const auto* Boat = Cast<ACarnivalBoat>(PC->GetPawn());
	const auto* Hover = Cast<ACarnivalHovercraft>(PC->GetPawn());
	if (!Bike && !Boat && !Hover) return;
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("[%s] Accelerate  [%s] Reverse  [%s] Steer"),
		*PC->GetActionKeyLabel(PC->ThrottleAction), *PC->GetActionKeyLabel(PC->BrakeReverseAction), *PC->GetActionKeyLabel(PC->SteerAction)));
	Lines.Add(FString::Printf(TEXT("[%s] Brake  [%s] Exit / recover"),
		*PC->GetActionKeyLabel(PC->BrakeAction), *PC->GetActionKeyLabel(PC->InteractMountAction)));
	if (Hover) Lines.Add(FString::Printf(TEXT("[%s] Boost  [%s] Strafe"),
		*PC->GetActionKeyLabel(PC->HandbrakeAction), *PC->GetActionKeyLabel(PC->RiderBalanceAction)));
	const float Width = FMath::Min(580.f, Canvas->ClipX - 40.f);
	DrawBoxWithText(20.f, Canvas->ClipY - 106.f, Width, 86.f, Bike ? TEXT("MOTORCYCLE") : Boat ? TEXT("BOAT") : TEXT("HOVERCRAFT"),
		Lines, FLinearColor(.025f,.035f,.05f,.9f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
}

void ACarnivalHUD::DrawSessionMenu(ACarnivalPlayerController* PC)
{
	const FString Confirm = PC->bUsingGamepad ? (PC->bPlayStationPrompts ? TEXT("Cross") : TEXT("A")) : TEXT("Enter");
	const FString Back = PC->bUsingGamepad ? (PC->bPlayStationPrompts ? TEXT("Circle") : TEXT("B")) : TEXT("Escape");
	TArray<FString> Lines;
	if (PC->bSessionRecordsOpen)
	{
		const auto* Campaign = PC->GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>();
		const TArray<FString> Records = PC->bJournalTab ? Campaign->GetJournalLines() : Campaign->GetInventoryLines();
		// One journal entry per page remains readable when wrapped at small resolutions.
		const int32 Page = FMath::Clamp(PC->RecordsPage, 0, FMath::Max(0, Records.Num() - 1));
		PC->RecordsPage = Page;
		Lines.Add(FString::Printf(TEXT("Entry %d / %d"), Page + 1, Records.Num()));
		if (Records.IsValidIndex(Page)) Lines.Add(Records[Page]);
		Lines.Add(TEXT("D-pad / arrows: up/down entries, left/right inventory/journal."));
		Lines.Add(FString::Printf(TEXT("[%s] Return to pause menu"), *Back));
		const float Width = FMath::Min(720.f, Canvas->ClipX - 40.f);
		DrawBoxWithText((Canvas->ClipX - Width) * .5f, Canvas->ClipY * .3f, Width, 170.f,
			PC->bJournalTab ? TEXT("SIGNAL JOURNAL") : TEXT("INVENTORY"), Lines,
			FLinearColor(.025f,.035f,.05f,.96f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
		return;
	}
	if (PC->SessionMenuConfirmation >= 0)
	{
		const TCHAR* Message = PC->SessionMenuConfirmation == 2 ? TEXT("Save over this slot?") :
			PC->SessionMenuConfirmation == 3 ? TEXT("Load this slot and replace current progress?") :
			PC->SessionMenuConfirmation == 4 ? TEXT("Restart the investigation?") :
			PC->SessionMenuConfirmation == 9 ? TEXT("Return to the nearest path?") : TEXT("Quit the game? Unsaved progress will be lost.");
		Lines.Add(Message);
		Lines.Add(FString::Printf(TEXT("[%s] Confirm   [%s] Cancel"), *Confirm, *Back));
	}
	else
	{
		auto Row = [&](int32 Index, const FString& Text) { Lines.Add((PC->SessionMenuSelection == Index ? TEXT("> ") : TEXT("  ")) + Text); };
		Row(0, TEXT("Resume"));
		Row(1, FString::Printf(TEXT("Slot %d: %s"), PC->SelectedSaveSlot + 1, *PC->SelectedSaveSummary));
		Row(2, TEXT("Save game"));
		Row(3, TEXT("Load game"));
		Row(4, TEXT("Retry investigation"));
		Row(5, TEXT("Settings"));
		Row(6, TEXT("Quit"));
		Row(7, TEXT("Inventory"));
		Row(8, TEXT("Campaign journal"));
		Row(9, TEXT("Return to path"));
		Lines.Add(TEXT(""));
		Lines.Add(FString::Printf(TEXT("D-pad / arrows: select. Left / right: slot. [%s] Choose. [%s] Resume."), *Confirm, *Back));
	}
	if (!PC->SessionMenuFeedback.IsEmpty()) Lines.Add(PC->SessionMenuFeedback);
	const float Width = FMath::Min(720.f, Canvas->ClipX - 40.f);
	const float Height = 48.f + Lines.Num() * 16.f;
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, (Canvas->ClipY - Height) * .5f, Width, Height,
		TEXT("PAUSED"), Lines, FLinearColor(.025f,.035f,.05f,.96f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
}

void ACarnivalHUD::DrawPlayerRecoveryPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Canvas || !Char || !PC || !Char->CanRecoverToSafePosition()) return;
	const FString Button = PC->GetActionKeyLabel(PC->CancelAction);
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("[%s] Return to safe ground"), *Button));
	const float Width = FMath::Min(360.f, Canvas->ClipX - 40.f);
	DrawBoxWithText(Canvas->ClipX - Width - 20.f, Canvas->ClipY - 84.f, Width, 56.f,
		TEXT("RECOVERY AVAILABLE"), Lines,
		FLinearColor(.025f,.035f,.05f,.92f), FLinearColor(1.f,.72f,.3f), FLinearColor::White);
}

void ACarnivalHUD::DrawStoryMissionOverlay(ACarnivalPlayerController* PC)
{
	if (!PC || !PC->GetGameInstance()) return;
	const UCarnivalMissionSubsystem* Mission = PC->GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>();
	if (!Mission) return;
	const auto* Campaign = PC->GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>();
	const bool bCampaignObjective = !Mission->IsMissionActive() && Campaign && !Campaign->GetObjective().IsEmpty();
	const FText Objective = bCampaignObjective ? Campaign->GetObjective() : Mission->GetCurrentObjective();
	const FText Feedback = Mission->GetPlayerFeedback();
	if (Objective.IsEmpty() && Feedback.IsEmpty()) return;

	TArray<FString> Lines;
	if (!Objective.IsEmpty()) Lines.Add(Objective.ToString());
	if (!Feedback.IsEmpty()) Lines.Add(Feedback.ToString());
	const bool bComplete = Mission->IsMissionComplete();
	const float Width = FMath::Min(680.f, Canvas->ClipX - 40.f);
	const float Height = Lines.Num() > 1 ? 78.f : 58.f;
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, 20.f, Width, Height,
		bCampaignObjective ? TEXT("THE SIGNAL NETWORK") : bComplete ? TEXT("INVESTIGATION COMPLETE") : TEXT("MISSING WORKER"), Lines,
		FLinearColor(.025f,.035f,.05f,.88f),
		bComplete ? FLinearColor(.35f,1.f,.55f) : FLinearColor(1.f,.78f,.35f),
		FLinearColor::White);
}

void ACarnivalHUD::DrawStoryInteractionPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Char || !PC) return;
	ACarnivalMissionInteractionActor* Target = Char->FindNearbyMissionInteraction();
	AActor* Door = Target ? nullptr : Char->FindNearbyDoor();
	if (!Target && !Door) return;
	const FString Button = PC->GetActionKeyLabel(PC->ContextInteractAction);
	FString Prompt;
	if (Target) Prompt = Target->GetPromptText().ToString();
	else Prompt = GetWorld()->GetSubsystem<UCarnivalDoorSubsystem>()->IsDoorOpen(Door) ? TEXT("Close door") : TEXT("Open door");
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("[%s] %s"), *Button, *Prompt));
	const float Width = FMath::Min(520.f, Canvas->ClipX - 40.f);
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, Canvas->ClipY - 88.f, Width, 58.f,
		TEXT("INTERACT"), Lines,
		FLinearColor(.025f,.035f,.05f,.92f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
}

void ACarnivalHUD::DrawRideInteraction(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
    if (auto* Car = PC ? Cast<ACarnivalBumperCar>(PC->GetPawn()) : nullptr)
    {
        const auto* Operation = Car->Arena ? Car->Arena->GetOperation() : nullptr;
        TArray<FString> Lines;
        if (Operation && Operation->State == ECarnivalOperationState::Running)
        {
            Lines.Add(FString::Printf(TEXT("[%s] Drive  |  [%s] Reverse  |  [%s] Steer"),
                *PC->GetActionKeyLabel(PC->ThrottleAction), *PC->GetActionKeyLabel(PC->BrakeReverseAction), *PC->GetActionKeyLabel(PC->SteerAction)));
            Lines.Add(FString::Printf(TEXT("[%s] Brake  |  [%s] Request stop and exit"),
                *PC->GetActionKeyLabel(PC->BrakeAction), *PC->GetActionKeyLabel(PC->InteractMountAction)));
        }
        else if (Operation && Operation->State == ECarnivalOperationState::Unloading)
            Lines.Add(TEXT("Waiting for a clear, safe place to exit."));
        else if (Operation && Operation->State == ECarnivalOperationState::Returning)
            Lines.Add(TEXT("Cars are stopping. Stay seated until you can exit."));
        else Lines.Add(TEXT("Wait for the attendant to start the cars."));
        const float Width = FMath::Min(620.f, Canvas->ClipX - 40.f);
        DrawBoxWithText((Canvas->ClipX - Width) * .5f, Canvas->ClipY - 120.f, Width, 95.f,
            TEXT("BUMPER CARS"), Lines, FLinearColor(.025f,.035f,.05f,.9f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
        return;
    }
	if (!Char || !PC) return;
	if (Char->FindNearbyMissionInteraction()) return;
	if (Char->NearbyActivity && Char->NearbyActivity->ActivityState != ECarnivalActivityState::Active) return;
	if (Char->ActiveActivity && (Char->ActiveActivity->ActivityState == ECarnivalActivityState::Completed
		|| Char->ActiveActivity->ActivityState == ECarnivalActivityState::Failed)) return;
	const bool bRiding = Char->RidePassenger && Char->RidePassenger->IsRiding();
	UCarnivalRideOperationComponent* Operation = Char->OperatingRide;
	if (!Operation && bRiding)
		Operation = Char->RidePassenger->GetCurrentRide()->FindComponentByClass<UCarnivalRideOperationComponent>();
	ACarnivalRideAttendant* Attendant = Operation ? Cast<ACarnivalRideAttendant>(Operation->Attendant) : Char->FindNearbyAttendant();
	if (!Operation && Attendant) Operation = Attendant->Operation;
	if (!Operation) return;
	const FString Board = PC->GetActionKeyLabel(PC->InteractMountAction);
	const FString Operate = PC->GetActionKeyLabel(PC->ContextInteractAction);
	const FString Start = PC->GetActionKeyLabel(PC->SprintAction);
	const FString Stop = PC->GetActionKeyLabel(PC->JumpVaultAction);
	const FString Leave = PC->GetActionKeyLabel(PC->CancelAction);
	TArray<FString> Lines;
	FString Status;
	switch (Operation->State)
	{
	case ECarnivalOperationState::Loading: Status = TEXT("Now boarding"); break;
	case ECarnivalOperationState::Securing: Status = TEXT("Attendant checking seats"); break;
	case ECarnivalOperationState::Running: Status = TEXT("Ride in progress"); break;
	case ECarnivalOperationState::Returning: Status = TEXT("Returning to the loading platform"); break;
	case ECarnivalOperationState::Unloading: Status = TEXT("Please exit the platform"); break;
	default: Status = TEXT("Ride closed"); break;
	}
	Lines.Add(Status);
	if (!Operation->IsReady()) Lines.Add(TEXT("This ride is not ready to board."));
	else if (Char->OperatingRide)
	{
		Lines.Add(FString::Printf(TEXT("[%s] Start  |  [%s] Return to platform"), *Start, *Stop));
		Lines.Add(FString::Printf(TEXT("[%s] Hand controls back to attendant"), *Leave));
	}
	else if (bRiding)
	{
		Lines.Add(Operation->State == ECarnivalOperationState::Returning
			? TEXT("Stay seated until the ride stops.")
			: FString::Printf(TEXT("[%s] Request exit  |  Look around freely"), *Board));
	}
	else
	{
		if (Operation->State == ECarnivalOperationState::Loading)
			Lines.Add(FString::Printf(TEXT("[%s] %s"), *Board,
				Operation->Experience == ECarnivalRideExperience::Walkthrough ? TEXT("Enter attraction") :
				Operation->Experience == ECarnivalRideExperience::Show ? TEXT("Start show") : TEXT("Board the ride")));
		else Lines.Add(TEXT("Please wait for the next boarding call."));
		if (Operation->bAllowPlayerOperation && !Operation->PlayerOperator)
			Lines.Add(FString::Printf(TEXT("[%s] Ask attendant to operate the ride"), *Operate));
	}
	const float Width = FMath::Min(540.f, Canvas->ClipX - 40.f);
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, Canvas->ClipY - 150.f, Width, 125.f,
		Attendant && !Attendant->RideName.IsEmpty() ? Attendant->RideName.ToString() : TEXT("Ride attendant"), Lines,
		FLinearColor(.025f,.035f,.05f,.9f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
}

void ACarnivalHUD::ToggleSettingsMenu()
{
	if (ACarnivalPlayerController* PC = Cast<ACarnivalPlayerController>(GetOwningPlayerController()))
	{
		PC->ToggleSettingsMenu();
		return;
	}
	bShowSettingsMenu = !bShowSettingsMenu;
}

void ACarnivalHUD::DrawTelemetry(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	TArray<FString> Lines;

	if (Char)
	{
		// Locomotion
		FString StateStr = TEXT("Unknown");
		switch (Char->LocomotionState)
		{
		case ECarnivalLocomotionState::Walking: StateStr = TEXT("Walking (200 cm/s)"); break;
		case ECarnivalLocomotionState::Jogging: StateStr = TEXT("Jogging (450 cm/s)"); break;
		case ECarnivalLocomotionState::Sprinting: StateStr = TEXT("Sprinting (750 cm/s)"); break;
		case ECarnivalLocomotionState::Crouching: StateStr = TEXT("Crouching (220 cm/s)"); break;
		case ECarnivalLocomotionState::Prone: StateStr = TEXT("Prone Crawl (120 cm/s)"); break;
		case ECarnivalLocomotionState::Vaulting: StateStr = TEXT("Parkour Vaulting"); break;
		case ECarnivalLocomotionState::Mantling: StateStr = TEXT("Parkour Mantling"); break;
		case ECarnivalLocomotionState::Swimming: StateStr = TEXT("Swimming (300 cm/s)"); break;
		case ECarnivalLocomotionState::RidingMotorcycle: StateStr = TEXT("Riding Motorcycle"); break;
		case ECarnivalLocomotionState::DrivingBoat: StateStr = TEXT("Piloting Boat"); break;
		case ECarnivalLocomotionState::PilotingHovercraft: StateStr = TEXT("Piloting Sci-Fi Hovercraft"); break;
		default: break;
		}

		float Speed = Char->GetVelocity().Size();
		Lines.Add(FString::Printf(TEXT("Locomotion: %s [Speed: %.0f]"), *StateStr, Speed));
		if (PC)
		{
			Lines.Add(FString::Printf(TEXT("Stance: [%s] Sprint | [%s] Crouch | [%s] Prone"), *PC->GetActionKeyLabel(PC->SprintAction), *PC->GetActionKeyLabel(PC->CrouchAction), *PC->GetActionKeyLabel(PC->ProneAction)));
			Lines.Add(FString::Printf(TEXT("Parkour: [%s] Jump / Vault / Mantle"), *PC->GetActionKeyLabel(PC->JumpVaultAction)));
		}

		// Weapon
		FString WeaponStr = TEXT("Unarmed (Fists / Kicks)");
		if (Char->CurrentWeapon)
		{
			switch (Char->CurrentWeapon->WeaponType)
			{
			case ECarnivalWeaponType::Sword: WeaponStr = TEXT("Sword & Shield"); break;
			case ECarnivalWeaponType::Revolver: WeaponStr = TEXT("Tesseract Revolver"); break;
			case ECarnivalWeaponType::Knife: WeaponStr = TEXT("Combat Knife"); break;
			default: break;
			}
		}
		Lines.Add(FString::Printf(TEXT("Weapon: %s"), *WeaponStr));
		if (PC) Lines.Add(FString::Printf(TEXT("Combat: [%s] Attack / Shoot / Combo"), *PC->GetActionKeyLabel(PC->AttackAction)));
	}

	const FString MountButton = PC ? PC->GetActionKeyLabel(PC->InteractMountAction) : TEXT("F");
	Lines.Add(TEXT("---"));
	Lines.Add(FString::Printf(TEXT("Motorcycle: [%s] Mount / Dismount / Recover"), *MountButton));
	if (PC && !Char)
	{
		Lines.Add(FString::Printf(TEXT("Driving: [%s] Throttle | [%s] Reverse | [%s] Steer"), *PC->GetActionKeyLabel(PC->ThrottleAction), *PC->GetActionKeyLabel(PC->BrakeReverseAction), *PC->GetActionKeyLabel(PC->SteerAction)));
		if (Cast<ACarnivalHovercraft>(PC->GetPawn()))
			Lines.Add(FString::Printf(TEXT("[%s] Boost | [%s] Strafe"), *PC->GetActionKeyLabel(PC->HandbrakeAction), *PC->GetActionKeyLabel(PC->RiderBalanceAction)));
	}
	Lines.Add(FString::Printf(TEXT("Other vehicles: [%s] Mount / Dismount"), *MountButton));
	Lines.Add(TEXT("Settings: [Escape] / [Options]"));

	DrawBoxWithText(20.0f, 100.0f, FMath::Min(600.f, Canvas->ClipX - 40.f), 48.f + Lines.Num() * 16.f,
		TEXT("CARNIVAL HERO CONTROLS & STATUS"),
		Lines,
		FLinearColor(0.02f, 0.04f, 0.08f, 0.75f),
		FLinearColor(0.2f, 0.9f, 1.0f, 1.0f),
		FLinearColor(0.9f, 0.9f, 0.9f, 1.0f));
}

void ACarnivalHUD::DrawFastTravelGuide()
{
	TArray<FString> Lines;
	Lines.Add(TEXT("[F1] Creepwood Carnival"));
	Lines.Add(TEXT("[F2] Haunted Mansion"));
	Lines.Add(TEXT("[F3] Town & Village"));
	Lines.Add(TEXT("[F4] Lighthouse & Ocean"));
	Lines.Add(TEXT("[F5] Medieval Castle"));
	Lines.Add(TEXT("[F6] Gladiator Arena"));
	Lines.Add(TEXT("[F7] Mars Outpost"));
	Lines.Add(TEXT("Press any F-key to travel instantly"));

	float Width = 320.0f;
	float X = Canvas->ClipX - Width - 20.0f;

	DrawBoxWithText(X, 20.0f, Width, 190.0f,
		TEXT("FAST TRAVEL DESTINATIONS"),
		Lines,
		FLinearColor(0.02f, 0.04f, 0.08f, 0.75f),
		FLinearColor(1.0f, 0.8f, 0.2f, 1.0f),
		FLinearColor(0.9f, 0.9f, 0.9f, 1.0f));
}

void ACarnivalHUD::DrawBuildModeHUD(ACarnivalPlayerCharacter* Char)
{
	if (!Char || !Char->BuildComponent)
	{
		return;
	}

	UCarnivalBuildComponent* BuildComp = Char->BuildComponent;
	bool bBuilding = BuildComp->bIsBuildModeActive;
	TArray<FString> Lines;

	if (bBuilding)
	{
		FString CatName = BuildComp->Categories.IsValidIndex(BuildComp->CurrentCategoryIndex) 
			? BuildComp->Categories[BuildComp->CurrentCategoryIndex].CategoryName 
			: TEXT("Default");

		FString PieceName = TEXT("None");
		if (BuildComp->Categories.IsValidIndex(BuildComp->CurrentCategoryIndex))
		{
			const auto& Pieces = BuildComp->Categories[BuildComp->CurrentCategoryIndex].Pieces;
			if (Pieces.IsValidIndex(BuildComp->CurrentPieceIndex) && Pieces[BuildComp->CurrentPieceIndex])
			{
				PieceName = Pieces[BuildComp->CurrentPieceIndex]->GetName();
			}
		}

		auto* PC = Cast<ACarnivalPlayerController>(GetOwningPlayerController());
		if (!PC) return;
		Lines.Add(FString::Printf(TEXT("[%s] Category: %s"), *PC->GetActionKeyLabel(PC->CycleCategoryAction), *CatName));
		Lines.Add(FString::Printf(TEXT("[%s / %s] Piece: %s"), *PC->GetActionKeyLabel(PC->CyclePiecePrevAction), *PC->GetActionKeyLabel(PC->CyclePieceNextAction), *PieceName));
		Lines.Add(FString::Printf(TEXT("[%s] Place  [%s] Demolish  [%s] Rotate"), *PC->GetActionKeyLabel(PC->AttackAction), *PC->GetActionKeyLabel(PC->SecondaryAction), *PC->GetActionKeyLabel(PC->RotatePieceAction)));
		Lines.Add(FString::Printf(TEXT("[%s] Exit building  |  Grid: %.0f cm"), *PC->GetActionKeyLabel(PC->ToggleBuildAction), BuildComp->GridSnapSize));
		Lines.Add(BuildComp->PlacementFeedback);
	}
	else
	{
		Lines.Add(TEXT("Press [B] to enter In-Game Build & Edit Mode"));
		Lines.Add(TEXT("Place modular Castle walls, Town houses, and Stunt Ramps live!"));
	}

	float Width = 520.0f;
	float Height = bBuilding ? 140.0f : 70.0f;
	float X = (Canvas->ClipX - Width) * 0.5f;
	float Y = Canvas->ClipY - Height - 25.0f;

	FLinearColor HeaderCol = bBuilding ? FLinearColor(0.2f, 1.0f, 0.4f, 1.0f) : FLinearColor(0.7f, 0.7f, 0.7f, 1.0f);
	FString Header = bBuilding ? TEXT("IN-GAME BUILD MODE [ACTIVE]") : TEXT("IN-GAME BUILD MODE [B]");

	DrawBoxWithText(X, Y, Width, Height,
		Header,
		Lines,
		FLinearColor(0.02f, 0.04f, 0.08f, 0.8f),
		HeaderCol,
		FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
}

void ACarnivalHUD::DrawSettingsMenu(ACarnivalPlayerController* PC)
{
	TArray<FString> Lines;
	const FString Selected = TEXT("> ");
	const FString Unselected = TEXT("  ");
	const FString Confirm = PC && PC->bPlayStationPrompts ? TEXT("Cross") : TEXT("A");
	const FString Back = PC && PC->bPlayStationPrompts ? TEXT("Circle") : TEXT("B");
	auto Row = [&](int32 Index, const FString& Text)
	{
		Lines.Add((PC && PC->SettingsMenuSelection == Index ? Selected : Unselected) + Text);
	};
	Row(0, FString::Printf(TEXT("Stick look speed: %.0f deg/sec"), PC ? PC->StickLookDegreesPerSecond : 120.f));
	Row(1, FString::Printf(TEXT("Stick dead zone: %.2f"), PC ? PC->StickDeadZone : .12f));
	Row(2, FString::Printf(TEXT("Vertical look: %s"), PC && PC->bInvertLookY ? TEXT("Inverted") : TEXT("Normal")));
	Row(3, FString::Printf(TEXT("Sprint: %s"), PC && PC->bSprintToggleMode ? TEXT("Toggle") : TEXT("Hold")));
	Row(4, TEXT("Restore input defaults"));
	Row(5, TEXT("Remap controls"));
    const auto* Audio = PC && PC->GetGameInstance() ? PC->GetGameInstance()->GetSubsystem<UCarnivalAudioSettingsSubsystem>() : nullptr;
    Row(6, FString::Printf(TEXT("Master volume: %d%%"), FMath::RoundToInt((Audio ? Audio->MasterVolume : 1.f) * 100.f)));
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("D-pad / arrows: select and adjust. ") + Confirm + TEXT(": select. ") + Back + TEXT(" / Options: close."));
	Lines.Add(TEXT("Keyboard: arrows, Enter, Escape. Mouse look remains direct."));

	float Width = FMath::Min(720.f, Canvas->ClipX - 40.f);
	if (PC && PC->bControlRemappingOpen) Lines = PC->GetControlRemappingLines();
	float Height = 48.f + Lines.Num() * 16.f;
	float X = (Canvas->ClipX - Width) * 0.5f;
	float Y = (Canvas->ClipY - Height) * 0.5f;

	DrawBoxWithText(X, Y, Width, Height,
		PC && PC->bControlRemappingOpen ? TEXT("REMAP CONTROLS") : TEXT("PLAYER SETTINGS"),
		Lines,
		FLinearColor(0.05f, 0.05f, 0.12f, 0.92f),
		FLinearColor(0.4f, 0.9f, 1.0f, 1.0f),
		FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
}

void ACarnivalHUD::DrawCrosshair()
{
	float CenterX = Canvas->ClipX * 0.5f;
	float CenterY = Canvas->ClipY * 0.5f;
	float Size = 4.0f;

	DrawRect(FLinearColor(1.0f, 1.0f, 1.0f, 0.7f), CenterX - Size * 0.5f, CenterY - Size * 0.5f, Size, Size);
}

void ACarnivalHUD::DrawBoxWithText(float X, float Y, float Width, float Height, const FString& Header, const TArray<FString>& Lines, const FLinearColor& BoxColor, const FLinearColor& HeaderColor, const FLinearColor& TextColor)
{
	UFont* Font = GEngine ? GEngine->GetSmallFont() : nullptr;
	if (!Canvas || !Font || Canvas->ClipX < 64.f || Canvas->ClipY < 64.f)
	{
		return;
	}
	const float OriginalWidth = Width;
	const float OriginalHeight = Height;
	const bool bCenteredX = FMath::IsNearlyEqual(X + Width * .5f, Canvas->ClipX * .5f, 2.f);
	const bool bCenteredY = FMath::IsNearlyEqual(Y + Height * .5f, Canvas->ClipY * .5f, 2.f);
	const bool bBottomAnchored = Y > Canvas->ClipY * .5f && !bCenteredY;
	Width = FMath::Clamp(Width, 40.f, Canvas->ClipX - 20.f);
	const float TextWidth = Width - 24.f;
	// Measure the actual font, including long remapped key labels. Break a long
	// token only when it cannot fit on its own line; never reduce the font size.
	auto Wrap = [this, Font, TextWidth](const FString& Text, float Scale, TArray<FString>& Out)
	{
		TArray<FString> Paragraphs;
		Text.ParseIntoArray(Paragraphs, TEXT("\n"), false);
		if (Paragraphs.IsEmpty()) Paragraphs.Add(TEXT(""));
		for (FString Remaining : Paragraphs)
		{
			if (Remaining.IsEmpty()) { Out.Add(TEXT("")); continue; }
			while (!Remaining.IsEmpty())
			{
				int32 Fit = 0, LastSpace = INDEX_NONE;
				for (int32 Index = 1; Index <= Remaining.Len(); ++Index)
				{
					float W = 0.f, H = 0.f;
					Canvas->StrLen(Font, Remaining.Left(Index), W, H);
					if (W * Scale > TextWidth) break;
					Fit = Index;
					if (FChar::IsWhitespace(Remaining[Index - 1])) LastSpace = Index;
				}
				if (Fit < Remaining.Len() && LastSpace > 0) Fit = LastSpace;
				Fit = FMath::Max(1, Fit);
				Out.Add(Remaining.Left(Fit).TrimEnd());
				Remaining = Remaining.Mid(Fit).TrimStart();
			}
		}
	};
	TArray<FString> HeaderLines, BodyLines;
	Wrap(Header, 1.1f, HeaderLines);
	for (const FString& Line : Lines) Wrap(Line, .95f, BodyLines);
	float FontWidth = 0.f, FontHeight = 0.f;
	Canvas->StrLen(Font, TEXT("Ag"), FontWidth, FontHeight);
	const float HeaderStep = FMath::Max(22.f, FontHeight * 1.1f + 3.f);
	const float BodyStep = FMath::Max(16.f, FontHeight * .95f + 2.f);
	const float MaxHeight = Canvas->ClipY - 20.f;
	const int32 MaxHeaderLines = FMath::Max(1, FMath::FloorToInt((MaxHeight - 22.f) / HeaderStep));
	if (HeaderLines.Num() > MaxHeaderLines) HeaderLines.SetNum(MaxHeaderLines);
	const float FixedHeight = 22.f + HeaderLines.Num() * HeaderStep;
	const int32 MaxBodyLines = FMath::Max(0, FMath::FloorToInt((MaxHeight - FixedHeight) / BodyStep));
	if (BodyLines.Num() > MaxBodyLines)
	{
		BodyLines.SetNum(MaxBodyLines);
		if (!BodyLines.IsEmpty()) BodyLines.Last() = TEXT("...");
	}
	Height = FMath::Min(MaxHeight, FMath::Max(Height, FixedHeight + BodyLines.Num() * BodyStep));
	if (bCenteredX) X += (OriginalWidth - Width) * .5f;
	if (bCenteredY) Y += (OriginalHeight - Height) * .5f;
	else if (bBottomAnchored) Y += OriginalHeight - Height;
	X = FMath::Clamp(X, 10.f, Canvas->ClipX - Width - 10.f);
	Y = FMath::Clamp(Y, 10.f, Canvas->ClipY - Height - 10.f);
	DrawRect(BoxColor, X, Y, Width, Height);
	DrawRect(HeaderColor, X, Y, Width, 3.f);
	float CurrentY = Y + 8.f;
	for (const FString& Line : HeaderLines)
	{
		DrawText(Line, HeaderColor, X + 12.f, CurrentY, Font, 1.1f, false);
		CurrentY += HeaderStep;
	}
	DrawRect(FLinearColor(HeaderColor.R, HeaderColor.G, HeaderColor.B, 0.3f), X + 12.0f, CurrentY, Width - 24.0f, 1.0f);
	CurrentY += 6.0f;
	for (const FString& Line : BodyLines)
	{
		DrawText(Line, TextColor, X + 12.0f, CurrentY, Font, 0.95f, false);
		CurrentY += BodyStep;
	}
}

void ACarnivalHUD::DrawActivityOverlay(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Char)
	{
		return;
	}
	const bool bMissionInteractionFocused = Char->FindNearbyMissionInteraction() != nullptr;
	const FString ContextButton = PC ? PC->GetActionKeyLabel(PC->ContextInteractAction) : TEXT("E");
	auto ActivityInstructions = [PC](FString Text)
	{
		if (!PC) return Text;
		FString Result;
		for (int32 Index = 0; Index < Text.Len(); ++Index)
		{
			if (Text[Index] == TEXT('[') && Index + 2 < Text.Len() && Text[Index + 2] == TEXT(']')
				&& Text[Index + 1] >= TEXT('1') && Text[Index + 1] <= TEXT('3'))
			{
				const UInputAction* Action = Text[Index + 1] == TEXT('1') ? PC->WeaponSlot1Action
					: Text[Index + 1] == TEXT('2') ? PC->WeaponSlot2Action : PC->WeaponSlot3Action;
				Result += FString::Printf(TEXT("[%s]"), *PC->GetActionKeyLabel(Action));
				Index += 2;
			}
			else Result += Text[Index];
		}
		return Result;
	};

	if (Char->ActiveActivity)
	{
		ACarnivalActivityBase* Act = Char->ActiveActivity;
		if (Act->ActivityState == ECarnivalActivityState::Active)
		{
			float Width = 520.0f;
			float Height = 80.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = 20.0f;
			if (PC && PC->GetGameInstance())
			{
				const UCarnivalMissionSubsystem* Mission = PC->GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>();
				if (Mission && Mission->IsMissionActive()) Y = 92.0f;
			}

			TArray<FString> Lines;
			Lines.Add(ActivityInstructions(Act->GetCurrentObjectiveText()));
			Lines.Add(FString::Printf(TEXT("Time Remaining: %.1fs  |  Score: %d"), Act->TimeRemaining, Act->CurrentScore));

			FLinearColor BorderCol = (Act->TimeRemaining < 10.0f) ? FLinearColor(1.0f, 0.2f, 0.2f, 1.0f) : FLinearColor(0.2f, 0.8f, 1.0f, 1.0f);
			DrawBoxWithText(X, Y, Width, Height,
				Act->GetDisplayTitle(),
				Lines,
				FLinearColor(0.02f, 0.04f, 0.08f, 0.88f),
				BorderCol,
				FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
		}
		else if (!bMissionInteractionFocused && Act->ActivityState == ECarnivalActivityState::Completed)
		{
			float Width = 520.0f;
			float Height = 120.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = (Canvas->ClipY - Height) * 0.5f;

			TArray<FString> Lines;
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->GetDisplayTitle()));
			Lines.Add(FString::Printf(TEXT("Completed in: %.1fs  |  Rating: %s"), Act->ElapsedTime, *Act->GetMedalRating()));
			Lines.Add(FString::Printf(TEXT("Final Score: %d points"), Act->CurrentScore));
			Lines.Add(FString::Printf(TEXT("Press [%s] to Dismiss"), *ContextButton));

			DrawBoxWithText(X, Y, Width, Height,
				TEXT("=== ACTIVITY COMPLETED! ==="),
				Lines,
				FLinearColor(0.02f, 0.06f, 0.03f, 0.92f),
				FLinearColor(0.2f, 1.0f, 0.3f, 1.0f),
				FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
		}
		else if (!bMissionInteractionFocused && Act->ActivityState == ECarnivalActivityState::Failed)
		{
			float Width = 480.0f;
			float Height = 100.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = (Canvas->ClipY - Height) * 0.5f;

			TArray<FString> Lines;
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->GetDisplayTitle()));
			Lines.Add(TEXT("Time expired! You didn't complete the objective in time."));
			Lines.Add(FString::Printf(TEXT("Press [%s] to Retry"), *ContextButton));

			DrawBoxWithText(X, Y, Width, Height,
				TEXT("=== CHALLENGE FAILED ==="),
				Lines,
				FLinearColor(0.08f, 0.02f, 0.02f, 0.92f),
				FLinearColor(1.0f, 0.2f, 0.2f, 1.0f),
				FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
		}
	}
	else if (!bMissionInteractionFocused && Char->NearbyActivity
		&& Char->NearbyActivity->ActivityState != ECarnivalActivityState::Active)
	{
		ACarnivalActivityBase* Act = Char->NearbyActivity;
		float Width = 560.0f;
		float Height = 75.0f;
		float X = (Canvas->ClipX - Width) * 0.5f;
		float Y = Canvas->ClipY - 190.0f;

		TArray<FString> Lines;
		Lines.Add(ActivityInstructions(Act->Description));

		DrawBoxWithText(X, Y, Width, Height,
			FString::Printf(TEXT("[%s] %s"), *ContextButton, *Act->GetDisplayTitle()),
			Lines,
			FLinearColor(0.04f, 0.03f, 0.08f, 0.88f),
			FLinearColor(1.0f, 0.8f, 0.2f, 1.0f),
			FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
	}
}
