// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalHUD.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalWeaponBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalActivityBase.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"

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

	DrawCrosshair();

	if (bShowHelpOverlay)
	{
		DrawTelemetry(Char, PC);
		DrawFastTravelGuide();
		DrawBuildModeHUD(Char);
	}

	DrawActivityOverlay(Char, PC);

	if (bShowSettingsMenu)
	{
		DrawSettingsMenu(PC);
	}
}

void ACarnivalHUD::ToggleSettingsMenu()
{
	bShowSettingsMenu = !bShowSettingsMenu;
	if (APlayerController* PC = GetOwningPlayerController())
	{
		PC->SetShowMouseCursor(bShowSettingsMenu);
		if (bShowSettingsMenu)
		{
			FInputModeGameAndUI Mode;
			PC->SetInputMode(Mode);
		}
		else
		{
			FInputModeGameOnly Mode;
			PC->SetInputMode(Mode);
		}
	}
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

	// Motorcycle
	// Vehicles
	Lines.Add(TEXT("---"));
	Lines.Add(TEXT("Motorcycle: [E] Mount / Dismount"));
	Lines.Add(TEXT("Driving: [W/S] Throttle/Reverse | [A/D] Steer | [Space] Brake"));
	Lines.Add(TEXT("Vehicles (Bike / Boat / Hover): [E] Mount / Dismount"));
	Lines.Add(TEXT("Driving: [W/S] Throttle/Reverse | [A/D] Steer | [Space] Brake / Boost"));
	Lines.Add(TEXT("Settings / Physics Toggle: [M] or [Tab]"));

	DrawBoxWithText(20.0f, 20.0f, 400.0f, 220.0f,
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
	Lines.Add(TEXT("1. MOTORCYCLE PHYSICS MODE:"));
	Lines.Add(TEXT("   - Arcade Mode: Responsive, auto-balancing, snappy arcade leaning."));
	Lines.Add(TEXT("   - Chaos Mode: 2-Wheel dynamic physics simulation, momentum, drift."));
	Lines.Add(TEXT("   Toggle with: [1] Arcade  |  [2] Chaos"));
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("2. FAST TRAVEL SHORTCUTS:"));
	Lines.Add(TEXT("   [F1] Carnival | [F2] Mansion | [F3] Town | [F4] Lighthouse"));
	Lines.Add(TEXT("   [F5] Castle   | [F6] Arena   | [F7] Mars"));
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("3. IN-GAME BUILDING SYSTEM:"));
	Lines.Add(TEXT("   Press [B] at any time to construct ramps, fortresses, and tracks."));
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("Press [M] or [Tab] to Close Settings Menu"));

	float Width = 580.0f;
	float Height = 300.0f;
	float X = (Canvas->ClipX - Width) * 0.5f;
	float Y = (Canvas->ClipY - Height) * 0.5f;

	DrawBoxWithText(X, Y, Width, Height,
		TEXT("SETTINGS & GAMEPLAY GUIDE"),
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

	if (Char->ActiveActivity)
	{
		ACarnivalActivityBase* Act = Char->ActiveActivity;
		if (Act->ActivityState == ECarnivalActivityState::Active)
		{
			float Width = 520.0f;
			float Height = 80.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = 20.0f;

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
		else if (Act->ActivityState == ECarnivalActivityState::Completed)
		{
			float Width = 520.0f;
			float Height = 120.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = (Canvas->ClipY - Height) * 0.5f;

			TArray<FString> Lines;
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->ActivityName));
			Lines.Add(FString::Printf(TEXT("Completed in: %.1fs  |  Rating: %s"), Act->ElapsedTime, *Act->GetMedalRating()));
			Lines.Add(FString::Printf(TEXT("Final Score: %d points"), Act->CurrentScore));
			Lines.Add(TEXT("Press [E] to Dismiss"));

			DrawBoxWithText(X, Y, Width, Height,
				TEXT("=== ACTIVITY COMPLETED! ==="),
				Lines,
				FLinearColor(0.02f, 0.06f, 0.03f, 0.92f),
				FLinearColor(0.2f, 1.0f, 0.3f, 1.0f),
				FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
		}
		else if (Act->ActivityState == ECarnivalActivityState::Failed)
		{
			float Width = 480.0f;
			float Height = 100.0f;
			float X = (Canvas->ClipX - Width) * 0.5f;
			float Y = (Canvas->ClipY - Height) * 0.5f;

			TArray<FString> Lines;
			Lines.Add(FString::Printf(TEXT("Challenge: %s"), *Act->ActivityName));
			Lines.Add(TEXT("Time expired! You didn't complete the objective in time."));
			Lines.Add(TEXT("Press [E] to Retry"));

			DrawBoxWithText(X, Y, Width, Height,
				TEXT("=== CHALLENGE FAILED ==="),
				Lines,
				FLinearColor(0.08f, 0.02f, 0.02f, 0.92f),
				FLinearColor(1.0f, 0.2f, 0.2f, 1.0f),
				FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
		}
	}
	else if (Char->NearbyActivity && Char->NearbyActivity->ActivityState != ECarnivalActivityState::Active)
	{
		ACarnivalActivityBase* Act = Char->NearbyActivity;
		float Width = 560.0f;
		float Height = 75.0f;
		float X = (Canvas->ClipX - Width) * 0.5f;
		float Y = Canvas->ClipY - 190.0f;

		TArray<FString> Lines;
		Lines.Add(FString::Printf(TEXT("%s - %s"), *Act->ActivityName, *Act->Description));
		Lines.Add(TEXT("Press [E] to Begin Challenge!"));

		DrawBoxWithText(X, Y, Width, Height,
			TEXT("[E] START ACTIVITY"),
			Lines,
			FLinearColor(0.04f, 0.03f, 0.08f, 0.88f),
			FLinearColor(1.0f, 0.8f, 0.2f, 1.0f),
			FLinearColor(0.95f, 0.95f, 0.95f, 1.0f));
	}
}
