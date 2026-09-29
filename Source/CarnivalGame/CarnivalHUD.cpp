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
#include "CarnivalWeaponBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalActivityBase.h"
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalMissionSubsystem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"

ACarnivalHUD::ACarnivalHUD()
{
	bShowHelpOverlay = true;
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
		DrawBuildModeHUD(Char);
#endif
	}

	DrawActivityOverlay(Char, PC);
	DrawStoryMissionOverlay(PC);
	DrawStoryInteractionPrompt(Char, PC);
	DrawPlayerRecoveryPrompt(Char, PC);
	DrawRideInteraction(Char, PC);

}

void ACarnivalHUD::DrawPlayerRecoveryPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Canvas || !Char || !PC || !Char->CanRecoverToSafePosition()) return;
	const FString Button = PC->bUsingGamepad
		? (PC->bPlayStationPrompts ? TEXT("Circle") : TEXT("B"))
		: TEXT("Backspace");
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
	const FText Objective = Mission->GetCurrentObjective();
	const FText Feedback = Mission->GetPlayerFeedback();
	if (Objective.IsEmpty() && Feedback.IsEmpty()) return;

	TArray<FString> Lines;
	if (!Objective.IsEmpty()) Lines.Add(Objective.ToString());
	if (!Feedback.IsEmpty()) Lines.Add(Feedback.ToString());
	const bool bComplete = Mission->IsMissionComplete();
	const float Width = FMath::Min(680.f, Canvas->ClipX - 40.f);
	const float Height = Lines.Num() > 1 ? 78.f : 58.f;
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, 20.f, Width, Height,
		bComplete ? TEXT("INVESTIGATION COMPLETE") : TEXT("MISSING WORKER"), Lines,
		FLinearColor(.025f,.035f,.05f,.88f),
		bComplete ? FLinearColor(.35f,1.f,.55f) : FLinearColor(1.f,.78f,.35f),
		FLinearColor::White);
}

void ACarnivalHUD::DrawStoryInteractionPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Char || !PC) return;
	ACarnivalMissionInteractionActor* Target = Char->FindNearbyMissionInteraction();
	if (!Target) return;
	const FString Button = PC->bUsingGamepad
		? TEXT("D-pad Right")
		: TEXT("E");
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("[%s] %s"), *Button, *Target->GetPromptText().ToString()));
	const float Width = FMath::Min(520.f, Canvas->ClipX - 40.f);
	DrawBoxWithText((Canvas->ClipX - Width) * .5f, Canvas->ClipY - 88.f, Width, 58.f,
		TEXT("INTERACT"), Lines,
		FLinearColor(.025f,.035f,.05f,.92f), FLinearColor(1.f,.78f,.35f), FLinearColor::White);
}

void ACarnivalHUD::DrawRideInteraction(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
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
	const bool bPad = PC->bUsingGamepad;
	const bool bPS = PC->bPlayStationPrompts;
	const FString Board = bPad ? (bPS ? TEXT("Triangle") : TEXT("Y")) : TEXT("F");
	const FString Operate = bPad ? TEXT("D-pad Right") : TEXT("E");
	const FString Start = bPad ? (bPS ? TEXT("Cross") : TEXT("A")) : TEXT("Shift");
	const FString Stop = bPad ? (bPS ? TEXT("Square") : TEXT("X")) : TEXT("Space");
	const FString Leave = bPad ? (bPS ? TEXT("Circle") : TEXT("B")) : TEXT("Backspace");
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
			Lines.Add(FString::Printf(TEXT("[%s] Board the ride"), *Board));
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
		Lines.Add(TEXT("Stance: [Shift] Sprint | [C] Crouch | [Z] Prone"));
		Lines.Add(TEXT("Parkour: [Space] Jump / Vault (<=115cm) / Mantle (<=230cm)"));

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
		Lines.Add(TEXT("Slots: [1] Sword | [2] Revolver | [3] Knife | [4] Unarmed"));
		Lines.Add(TEXT("Combat: [LMB] Attack / Shoot / Combo"));
	}

	const bool bPad = PC && PC->bUsingGamepad;
	const bool bPlayStation = PC && PC->bPlayStationPrompts;
	const FString MountButton = bPad ? (bPlayStation ? TEXT("Triangle") : TEXT("Y")) : TEXT("F");
	Lines.Add(TEXT("---"));
	Lines.Add(FString::Printf(TEXT("Motorcycle: [%s] Mount / Dismount / Recover"), *MountButton));
	Lines.Add(bPad
		? TEXT("Driving: [R2/L2] Throttle/Brake | [Left Stick] Steer")
		: TEXT("Driving: [W/S] Throttle/Reverse | [A/D] Steer | [Space] Brake"));
	Lines.Add(FString::Printf(TEXT("Other vehicles: [%s] Mount / Dismount"), *MountButton));
	Lines.Add(TEXT("Settings / Physics Toggle: [M] or [Tab]"));

	DrawBoxWithText(20.0f, 20.0f, 420.0f, 240.0f,
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

		Lines.Add(FString::Printf(TEXT("Category [T]: %s"), *CatName));
		Lines.Add(FString::Printf(TEXT("Piece [Q/E/Scroll]: %s"), *PieceName));
		Lines.Add(TEXT("Action: [LMB] Place Piece | [RMB] Demolish Aimed"));
		Lines.Add(TEXT("Transform: [R] Rotate 90 deg | Grid Snap: 100cm"));
		Lines.Add(TEXT("Exit: [B] to Close Build Mode"));
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
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("D-pad / arrows: select and adjust. ") + Confirm + TEXT(": select. ") + Back + TEXT(" / Options: close."));
	Lines.Add(TEXT("Keyboard: arrows, Enter, Escape. Mouse look remains direct."));

	float Width = FMath::Min(720.f, Canvas->ClipX - 40.f);
	float Height = 190.0f;
	float X = (Canvas->ClipX - Width) * 0.5f;
	float Y = (Canvas->ClipY - Height) * 0.5f;

	DrawBoxWithText(X, Y, Width, Height,
		TEXT("PLAYER SETTINGS"),
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
	// Background box
	DrawRect(BoxColor, X, Y, Width, Height);

	// Accent border on top
	DrawRect(HeaderColor, X, Y, Width, 3.0f);

	UFont* Font = GEngine->GetSmallFont();
	if (!Font)
	{
		return;
	}

	float CurrentY = Y + 8.0f;

	// Draw Header
	DrawText(Header, HeaderColor, X + 12.0f, CurrentY, Font, 1.1f, false);
	CurrentY += 22.0f;

	// Draw separator line
	DrawRect(FLinearColor(HeaderColor.R, HeaderColor.G, HeaderColor.B, 0.3f), X + 12.0f, CurrentY, Width - 24.0f, 1.0f);
	CurrentY += 6.0f;

	// Draw content lines
	for (const FString& Line : Lines)
	{
		DrawText(Line, TextColor, X + 12.0f, CurrentY, Font, 0.95f, false);
		CurrentY += 16.0f;
	}
}

void ACarnivalHUD::DrawActivityOverlay(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC)
{
	if (!Char)
	{
		return;
	}
	const bool bMissionInteractionFocused = Char->FindNearbyMissionInteraction() != nullptr;
	const FString ContextButton = PC && PC->bUsingGamepad ? TEXT("D-pad Right") : TEXT("E");

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
			Lines.Add(Act->GetCurrentObjectiveText());
			Lines.Add(FString::Printf(TEXT("Time Remaining: %.1fs  |  Score: %d"), Act->TimeRemaining, Act->CurrentScore));

			FLinearColor BorderCol = (Act->TimeRemaining < 10.0f) ? FLinearColor(1.0f, 0.2f, 0.2f, 1.0f) : FLinearColor(0.2f, 0.8f, 1.0f, 1.0f);
			DrawBoxWithText(X, Y, Width, Height,
				FString::Printf(TEXT("ACTIVITY: %s"), *Act->ActivityName.ToUpper()),
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
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->ActivityName));
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
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->ActivityName));
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
		Lines.Add(FString::Printf(TEXT("%s - %s"), *Act->ActivityName, *Act->Description));
		Lines.Add(FString::Printf(TEXT("Press [%s] to Begin Challenge!"), *ContextButton));

		DrawBoxWithText(X, Y, Width, Height,
			FString::Printf(TEXT("[%s] START ACTIVITY"), *ContextButton),
			Lines,
			FLinearColor(0.04f, 0.03f, 0.08f, 0.88f),
			FLinearColor(1.0f, 0.8f, 0.2f, 1.0f),
			FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
	}
}
