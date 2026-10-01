// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalPlayerController.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalBumperCar.h"
#include "CarnivalAudioSettingsSubsystem.h"
#include "CarnivalActivityBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalMissionSubsystem.h"
#include "CarnivalSaveSubsystem.h"
#include "CarnivalRideOperationComponent.h"
#include "CarnivalHUD.h"
#include "InputKeyEventArgs.h"
#include "Blueprint/UserWidget.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/ConfigCacheIni.h"

namespace
{
constexpr const TCHAR* CarnivalInputSettingsSection = TEXT("Carnival.InputSettings");
constexpr int32 CarnivalInputSettingsRows = 7;

FVector2D ApplyRadialDeadZone(FVector2D Value, float DeadZone)
{
	Value = Value.GetClampedToMaxSize(1.f);
	const float Magnitude = Value.Size();
	if (Magnitude <= DeadZone || Magnitude <= UE_SMALL_NUMBER)
	{
		return FVector2D::ZeroVector;
	}
	return Value.GetSafeNormal() * FMath::Clamp((Magnitude - DeadZone) / (1.f - DeadZone), 0.f, 1.f);
}

float ApplyAxisDeadZone(float Value, float DeadZone)
{
	const float Magnitude = FMath::Abs(Value);
	if (Magnitude <= DeadZone) return 0.f;
	return FMath::Sign(Value) * FMath::Clamp((Magnitude - DeadZone) / (1.f - DeadZone), 0.f, 1.f);
}
}

ACarnivalPlayerController::ACarnivalPlayerController()
{
	SettingsMenuWidget = nullptr;
}

bool ACarnivalPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
	const bool bMeaningfulActivity = Params.Event == IE_Pressed || Params.Event == IE_Repeat
		|| (Params.Event == IE_Axis && FMath::Abs(Params.AmountDepressed) > .2f);
	if (bControllerDisconnectPaused && bMeaningfulActivity)
	{
		// Resume on the first deliberate input from either a reconnected controller or keyboard/mouse.
		bControllerDisconnectPaused = false;
		SetPause(bSessionMenuOpen || bSettingsMenuOpen);
	}

	// Stick drift should not replace keyboard prompts.
	if (Params.Event != IE_Released && FMath::Abs(Params.AmountDepressed) > .2)
		bUsingGamepad = Params.IsGamepad();
	if (Params.IsGamepad() && Params.Event != IE_Released && FMath::Abs(Params.AmountDepressed) > .2f && Params.InputDevice.IsValid())
		LastActiveGamepadDeviceId = Params.InputDevice;

	if (bSessionMenuOpen)
	{
		HandleSessionMenuInput(Params);
		return true;
	}
	if (bSettingsMenuOpen)
	{
		if (bControlRemappingOpen) HandleControlRemappingInput(Params);
		else HandleSettingsMenuInput(Params);
		return true;
	}

	if (Params.Event == IE_Pressed && (Params.Key == EKeys::Escape || Params.Key == EKeys::Gamepad_Special_Right))
	{
		ToggleSessionMenu();
		return true;
	}

	return Super::InputKey(Params);
}

void ACarnivalPlayerController::ToggleSessionMenu()
{
	if (bSessionMenuOpen)
	{
		bSessionMenuOpen = false;
		bSessionRecordsOpen = false;
		SessionMenuConfirmation = -1;
		FlushPressedKeys();
		SetPause(false);
		return;
	}
	if (!SetPause(true)) return;
	ClearCurrentPawnInputs(false);
	bSessionMenuOpen = true;
	bSessionRecordsOpen = false;
	SessionMenuSelection = 0;
	SessionMenuConfirmation = -1;
	SessionMenuFeedback.Reset();
	RefreshSaveSummary();
}

void ACarnivalPlayerController::RefreshSaveSummary()
{
	const auto* Saves = GetGameInstance() ? GetGameInstance()->GetSubsystem<UCarnivalSaveSubsystem>() : nullptr;
	SelectedSaveSummary = Saves ? Saves->GetSlotSummary(SelectedSaveSlot) : TEXT("Unavailable");
}

void ACarnivalPlayerController::HandleSessionMenuInput(const FInputKeyEventArgs& Params)
{
	if (Params.Event != IE_Pressed && Params.Event != IE_Repeat) return;
	const FKey Key = Params.Key;
	if (bSessionRecordsOpen)
	{
		if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_Special_Right)
			bSessionRecordsOpen = false;
		else if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left) { bJournalTab = !bJournalTab; RecordsPage = 0; }
		else if (Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right) { bJournalTab = !bJournalTab; RecordsPage = 0; }
		else if (Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up) RecordsPage = FMath::Max(0, RecordsPage - 1);
		else if (Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down) RecordsPage = FMath::Min(100, RecordsPage + 1);
		return;
	}
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_Special_Right)
	{
		if (SessionMenuConfirmation >= 0) SessionMenuConfirmation = -1;
		else ToggleSessionMenu();
		return;
	}
	if (SessionMenuConfirmation < 0)
	{
		if (Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up) SessionMenuSelection = (SessionMenuSelection + 9) % 10;
		else if (Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down) SessionMenuSelection = (SessionMenuSelection + 1) % 10;
		else if (SessionMenuSelection == 1)
		{
			if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left) SelectedSaveSlot = (SelectedSaveSlot + 2) % 3;
			if (Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right) SelectedSaveSlot = (SelectedSaveSlot + 1) % 3;
			if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right) RefreshSaveSummary();
		}
	}
	// Holding confirm cannot both open and accept a destructive confirmation.
	if (Params.Event == IE_Pressed && (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom))
		ActivateSessionMenuChoice();
}

void ACarnivalPlayerController::ActivateSessionMenuChoice()
{
	const int32 Choice = SessionMenuConfirmation >= 0 ? SessionMenuConfirmation : SessionMenuSelection;
	if (Choice == 0) { ToggleSessionMenu(); return; }
	if (Choice == 1) { SelectedSaveSlot = (SelectedSaveSlot + 1) % 3; RefreshSaveSummary(); return; }
	if (Choice == 7 || Choice == 8)
	{
		bSessionRecordsOpen = true; bJournalTab = Choice == 8; RecordsPage = 0; return;
	}
	if (Choice == 5)
	{
		bSessionMenuOpen = false;
		bReturnToSessionMenu = true;
		ToggleSettingsMenu();
		return;
	}
	if (SessionMenuConfirmation < 0)
	{
		SessionMenuConfirmation = Choice;
		return;
	}
	SessionMenuConfirmation = -1;
	auto* SessionCharacter = Cast<ACarnivalPlayerCharacter>(GetPawn());
	auto* Saves = GetGameInstance()->GetSubsystem<UCarnivalSaveSubsystem>();
	if (Choice == 2 || Choice == 3)
	{
		const bool bSuccess = Choice == 2 ? Saves->SaveSlot(SelectedSaveSlot, SessionCharacter) : Saves->LoadSlot(SelectedSaveSlot, SessionCharacter);
		SessionMenuFeedback = Saves->LastResult;
		RefreshSaveSummary();
		if (bSuccess && Choice == 3)
		{
			GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>()->ShowPlayerFeedback(FText::FromString(Saves->LastResult));
			ToggleSessionMenu();
		}
	}
	else if (Choice == 4)
	{
		const bool bSuccess = SessionCharacter && !SessionCharacter->IsUsingRide() && !SessionCharacter->MountedMotorcycle
			&& !SessionCharacter->MountedBoat && !SessionCharacter->MountedHovercraft && !SessionCharacter->IsParkourTraversing()
			&& !SessionCharacter->ActiveActivity && GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>()->RetryStoryMission();
		SessionMenuFeedback = bSuccess ? TEXT("Investigation restarted. Return to the mansion.") : TEXT("Finish the current action before retrying an active investigation.");
	}
	else if (Choice == 6) UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
	else if (Choice == 9)
	{
		if (SessionCharacter && SessionCharacter->ReturnToNearestRoute())
		{
			GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>()->ShowPlayerFeedback(FText::FromString(TEXT("Returned to the nearest path.")));
			ToggleSessionMenu();
		}
		else SessionMenuFeedback = TEXT("Leave the ride, vehicle or activity first. No clear path point was found nearby.");
	}
}

void ACarnivalPlayerController::OnUnPossess()
{
	ClearCurrentPawnInputs();
	Super::OnUnPossess();
}

void ACarnivalPlayerController::ClearCurrentPawnInputs(bool bLeaveRideOperator)
{
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) Car->ClearControlInputs();
	OtherVehicleThrottle = 0.f;
	OtherVehicleReverse = 0.f;
	if (auto* Boat = Cast<ACarnivalBoat>(GetPawn()))
	{
		Boat->InputThrottle(0.f);
		Boat->InputSteering(0.f);
		Boat->InputBrake(0.f);
	}
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn()))
	{
		Hover->InputThrottle(0.f);
		Hover->InputSteering(0.f);
		Hover->InputStrafe(0.f);
		Hover->InputBoost(false);
	}
	if (auto* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputThrottle(0.f);
		Bike->InputSteering(0.f);
		Bike->InputBrake(0.f);
		Bike->InputBrakeReverse(0.f);
		Bike->InputHandbrake(false);
		Bike->InputRiderBalance(0.f);
	}
	if (auto* CarnivalCharacter = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		CarnivalCharacter->StopSprinting();
		CarnivalCharacter->StopJumping();
		CarnivalCharacter->SetSwimUpHeld(false);
		CarnivalCharacter->SetSwimDownHeld(false);
		CarnivalCharacter->ConsumeMovementInputVector();
		if (bLeaveRideOperator) CarnivalCharacter->LeaveRideOperator();
	}
	bSprintToggleActive = false;
	FlushPressedKeys();
}

void ACarnivalPlayerController::LoadPlayerInputSettings()
{
	if (!GConfig) return;
	GConfig->GetFloat(CarnivalInputSettingsSection, TEXT("StickLookDegreesPerSecond"), StickLookDegreesPerSecond, GGameUserSettingsIni);
	GConfig->GetFloat(CarnivalInputSettingsSection, TEXT("StickDeadZone"), StickDeadZone, GGameUserSettingsIni);
	GConfig->GetBool(CarnivalInputSettingsSection, TEXT("InvertLookY"), bInvertLookY, GGameUserSettingsIni);
	GConfig->GetBool(CarnivalInputSettingsSection, TEXT("SprintToggleMode"), bSprintToggleMode, GGameUserSettingsIni);
	StickLookDegreesPerSecond = FMath::Clamp(StickLookDegreesPerSecond, 60.f, 240.f);
	StickDeadZone = FMath::Clamp(StickDeadZone, .05f, .3f);
}

void ACarnivalPlayerController::SavePlayerInputSettings() const
{
	if (!GConfig) return;
	GConfig->SetFloat(CarnivalInputSettingsSection, TEXT("StickLookDegreesPerSecond"), StickLookDegreesPerSecond, GGameUserSettingsIni);
	GConfig->SetFloat(CarnivalInputSettingsSection, TEXT("StickDeadZone"), StickDeadZone, GGameUserSettingsIni);
	GConfig->SetBool(CarnivalInputSettingsSection, TEXT("InvertLookY"), bInvertLookY, GGameUserSettingsIni);
	GConfig->SetBool(CarnivalInputSettingsSection, TEXT("SprintToggleMode"), bSprintToggleMode, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

void ACarnivalPlayerController::HandleSettingsMenuInput(const FInputKeyEventArgs& Params)
{
	if (Params.Event != IE_Pressed && Params.Event != IE_Repeat) return;
	const FKey Key = Params.Key;
	if (Key == EKeys::Escape || Key == EKeys::M || Key == EKeys::Tab
		|| Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
	{
		ToggleSettingsMenu();
		return;
	}
	if (Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Up || Key == EKeys::W)
	{
		SettingsMenuSelection = (SettingsMenuSelection + CarnivalInputSettingsRows - 1) % CarnivalInputSettingsRows;
	}
	else if (Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Down || Key == EKeys::S)
	{
		SettingsMenuSelection = (SettingsMenuSelection + 1) % CarnivalInputSettingsRows;
	}
	else if (Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Left || Key == EKeys::A)
	{
		AdjustSelectedSetting(-1);
	}
	else if (Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Right || Key == EKeys::D)
	{
		AdjustSelectedSetting(1);
	}
	else if (Key == EKeys::Gamepad_FaceButton_Bottom || Key == EKeys::Enter || Key == EKeys::SpaceBar)
	{
		ActivateSelectedSetting();
	}
}

void ACarnivalPlayerController::AdjustSelectedSetting(int32 Direction)
{
	if (Direction == 0) return;
	switch (SettingsMenuSelection)
	{
	case 0:
		StickLookDegreesPerSecond = FMath::Clamp(StickLookDegreesPerSecond + Direction * 20.f, 60.f, 240.f);
		break;
	case 1:
		StickDeadZone = FMath::Clamp(StickDeadZone + Direction * .025f, .05f, .3f);
		break;
	case 6:
        if (auto* Audio = GetGameInstance() ? GetGameInstance()->GetSubsystem<UCarnivalAudioSettingsSubsystem>() : nullptr)
            Audio->SetMasterVolume(Audio->MasterVolume + Direction * .1f);
        return;
	default:
		return;
	}
	SavePlayerInputSettings();
}

void ACarnivalPlayerController::ActivateSelectedSetting()
{
	switch (SettingsMenuSelection)
	{
	case 2:
		bInvertLookY = !bInvertLookY;
		break;
	case 3:
		bSprintToggleMode = !bSprintToggleMode;
		bSprintToggleActive = false;
		if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn())) Char->StopSprinting();
		break;
	case 4:
		ResetPlayerInputSettings();
		return;
	case 5:
		OpenControlRemapping(bUsingGamepad);
		return;
	default:
		return;
	}
	SavePlayerInputSettings();
}

void ACarnivalPlayerController::OpenControlRemapping(bool bGamepad)
{
	if (!bSettingsMenuOpen) ToggleSettingsMenu();
	bControlRemappingOpen = true;
	bCapturingControl = false;
	bRemapGamepad = bGamepad;
	ControlRemappingSelection = 0;
	ControlRemappingFeedback.Reset();
}

void ACarnivalPlayerController::ResetPlayerInputSettings()
{
	StickLookDegreesPerSecond = 120.f;
	StickDeadZone = .12f;
	bInvertLookY = false;
	bSprintToggleMode = false;
	bSprintToggleActive = false;
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn())) Char->StopSprinting();
	SavePlayerInputSettings();
}

void ACarnivalPlayerController::BeginPlay()
{
	Super::BeginPlay();
	LoadPlayerInputSettings();
    if (auto* Audio = GetGameInstance() ? GetGameInstance()->GetSubsystem<UCarnivalAudioSettingsSubsystem>() : nullptr)
        Audio->ApplyToWorld(GetWorld());
	InitializeControlRemapping();
	if (UGameInstance* GameInstance = GetGameInstance())
		GameInstance->OnInputDeviceConnectionChange.AddDynamic(this, &ACarnivalPlayerController::HandleInputDeviceConnectionChange);

	RebuildControlMappings();
}

void ACarnivalPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UGameInstance* GameInstance = GetGameInstance())
		GameInstance->OnInputDeviceConnectionChange.RemoveDynamic(this, &ACarnivalPlayerController::HandleInputDeviceConnectionChange);
	Super::EndPlay(EndPlayReason);
}

void ACarnivalPlayerController::HandleInputDeviceConnectionChange(EInputDeviceConnectionState NewConnectionState, FPlatformUserId PlatformUserId, FInputDeviceId InputDeviceId)
{
	if (NewConnectionState != EInputDeviceConnectionState::Disconnected
		|| !bUsingGamepad
		|| !LastActiveGamepadDeviceId.IsValid()
		|| InputDeviceId != LastActiveGamepadDeviceId)
	{
		return;
	}

	LastActiveGamepadDeviceId = INPUTDEVICEID_NONE;
	bUsingGamepad = false;
	ClearCurrentPawnInputs();
	bControllerDisconnectPaused = SetPause(true);
	if (!bControllerDisconnectPaused)
	{
		UE_LOG(LogTemp, Warning, TEXT("Controller disconnected, but the active game mode refused to pause."));
	}
}

void ACarnivalPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (InPawn && (InPawn->IsA<ACarnivalMotorcycle>() || InPawn->IsA<ACarnivalBoat>() || InPawn->IsA<ACarnivalHovercraft>() || InPawn->IsA<ACarnivalBumperCar>()))
		{
			if (DefaultMappingContext)
			{
				Subsystem->RemoveMappingContext(DefaultMappingContext);
			}
			if (MotorcycleMappingContext)
			{
				Subsystem->AddMappingContext(MotorcycleMappingContext, 0);
			}
		}
		else
		{
			if (MotorcycleMappingContext)
			{
				Subsystem->RemoveMappingContext(MotorcycleMappingContext);
			}
			if (DefaultMappingContext)
			{
				Subsystem->AddMappingContext(DefaultMappingContext, 0);
			}
		}
	}
}

void ACarnivalPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent))
	{
		// Locomotion
		if (MoveAction)
		{
			EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnMove);
		}
		if (LookAction)
		{
			EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnLook);
		}
		if (LookStickAction)
			EnhancedInputComponent->BindAction(LookStickAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnLookStick);
		if (ContextInteractAction)
			EnhancedInputComponent->BindAction(ContextInteractAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnContextInteract);
		if (CancelAction)
			EnhancedInputComponent->BindAction(CancelAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnCancel);
		if (JumpVaultAction)
		{
			EnhancedInputComponent->BindAction(JumpVaultAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnJumpVault);
			EnhancedInputComponent->BindAction(JumpVaultAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnJumpVaultReleased);
			EnhancedInputComponent->BindAction(JumpVaultAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnJumpVaultReleased);
		}
		if (SprintAction)
		{
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnStartSprint);
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnStopSprint);
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnStopSprint);
		}
		if (CrouchAction)
		{
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnToggleCrouch);
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnCrouchReleased);
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnCrouchReleased);
		}
		if (ProneAction)
		{
			EnhancedInputComponent->BindAction(ProneAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnToggleProne);
		}
		if (InteractMountAction)
		{
			EnhancedInputComponent->BindAction(InteractMountAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnInteractMount);
		}
		// These legacy combat/build bindings are for in-editor project testing only.
#if WITH_EDITOR
		if (AttackAction)
		{
			EnhancedInputComponent->BindAction(AttackAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnAttack);
		}
		if (SecondaryAction)
		{
			EnhancedInputComponent->BindAction(SecondaryAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnSecondary);
		}
		if (ToggleBuildAction)
		{
			EnhancedInputComponent->BindAction(ToggleBuildAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnToggleBuild);
		}
		if (RotatePieceAction)
		{
			EnhancedInputComponent->BindAction(RotatePieceAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnRotatePiece);
		}
		if (CyclePieceNextAction)
		{
			EnhancedInputComponent->BindAction(CyclePieceNextAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnCyclePieceNext);
		}
		if (CyclePiecePrevAction)
		{
			EnhancedInputComponent->BindAction(CyclePiecePrevAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnCyclePiecePrev);
		}
		if (CycleCategoryAction)
		{
			EnhancedInputComponent->BindAction(CycleCategoryAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnCycleCategory);
		}

		// Weapon slots
		if (WeaponSlot1Action)
		{
			EnhancedInputComponent->BindAction(WeaponSlot1Action, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnWeaponSlot1);
		}
		if (WeaponSlot2Action)
		{
			EnhancedInputComponent->BindAction(WeaponSlot2Action, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnWeaponSlot2);
		}
		if (WeaponSlot3Action)
		{
			EnhancedInputComponent->BindAction(WeaponSlot3Action, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnWeaponSlot3);
		}
		if (WeaponSlot0Action)
		{
			EnhancedInputComponent->BindAction(WeaponSlot0Action, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnWeaponSlot0);
		}
#endif

		// Settings Menu
		if (SettingsMenuAction)
		{
			EnhancedInputComponent->BindAction(SettingsMenuAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::ToggleSettingsMenu);
		}

		// Fast-travel hotkeys are editor-only; packaged travel follows the authored routes.
#if WITH_EDITOR
		if (TravelCarnivalAction)
		{
			EnhancedInputComponent->BindAction(TravelCarnivalAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelCarnival);
		}
		if (TravelMansionAction)
		{
			EnhancedInputComponent->BindAction(TravelMansionAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelMansion);
		}
		if (TravelTownAction)
		{
			EnhancedInputComponent->BindAction(TravelTownAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelTown);
		}
		if (TravelLighthouseAction)
		{
			EnhancedInputComponent->BindAction(TravelLighthouseAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelLighthouse);
		}
		if (TravelCastleAction)
		{
			EnhancedInputComponent->BindAction(TravelCastleAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelCastle);
		}
		if (TravelArenaAction)
		{
			EnhancedInputComponent->BindAction(TravelArenaAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelArena);
		}
		if (TravelMarsAction)
		{
			EnhancedInputComponent->BindAction(TravelMarsAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnTravelMars);
		}
#endif

		// Motorcycle driving
		if (ThrottleAction)
		{
			EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnThrottle);
			EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnThrottle);
			EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnThrottle);
		}
		if (SteerAction)
		{
			EnhancedInputComponent->BindAction(SteerAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnSteer);
			EnhancedInputComponent->BindAction(SteerAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnSteer);
			EnhancedInputComponent->BindAction(SteerAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnSteer);
		}
		if (BrakeAction)
		{
			EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnBrake);
			EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnBrake);
			EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnBrake);
		}
		if (BrakeReverseAction)
		{
			EnhancedInputComponent->BindAction(BrakeReverseAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnBrakeReverse);
			EnhancedInputComponent->BindAction(BrakeReverseAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnBrakeReverse);
			EnhancedInputComponent->BindAction(BrakeReverseAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnBrakeReverse);
		}
		if (HandbrakeAction)
		{
			EnhancedInputComponent->BindAction(HandbrakeAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnHandbrake);
			EnhancedInputComponent->BindAction(HandbrakeAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnHandbrake);
			EnhancedInputComponent->BindAction(HandbrakeAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnHandbrake);
		}
		if (RiderBalanceAction)
		{
			EnhancedInputComponent->BindAction(RiderBalanceAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnRiderBalance);
			EnhancedInputComponent->BindAction(RiderBalanceAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnRiderBalance);
			EnhancedInputComponent->BindAction(RiderBalanceAction, ETriggerEvent::Canceled, this, &ACarnivalPlayerController::OnRiderBalance);
		}
	}
}

void ACarnivalPlayerController::OnMove(const FInputActionValue& Value)
{
	FVector2D MovementVector = ApplyRadialDeadZone(Value.Get<FVector2D>(), StickDeadZone);
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->MoveForward(MovementVector.Y);
		Char->MoveRight(MovementVector.X);
	}
}

void ACarnivalPlayerController::OnLook(const FInputActionValue& Value)
{
	FVector2D LookVector = Value.Get<FVector2D>();
	AddYawInput(LookVector.X);
	AddPitchInput(bInvertLookY ? -LookVector.Y : LookVector.Y);
}

void ACarnivalPlayerController::OnJumpVault()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (IsValid(Char->OperatingRide)) { Char->OperatingRide->OperatorStop(Char); return; }
		if (Char->IsUsingRide()) return;
		// In water, jump is held to swim up (and lifts off the bottom).
		if (Char->IsInWaterVolume()) { Char->SetSwimUpHeld(true); return; }
		if (!Char->TryLadderClimb() && !Char->TryVaultOrMantle())
		{
			Char->Jump();
		}
	}
}

void ACarnivalPlayerController::OnStartSprint()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (IsValid(Char->OperatingRide)) { Char->OperatingRide->OperatorStart(Char); return; }
		if (bSprintToggleMode)
		{
			bSprintToggleActive = !bSprintToggleActive;
			if (bSprintToggleActive) Char->StartSprinting();
			else Char->StopSprinting();
		}
		else
		{
			Char->StartSprinting();
		}
	}
}

void ACarnivalPlayerController::OnLookStick(const FInputActionValue& Value)
{
	if (IsLookInputIgnored()) return;
	FVector2D Stick = ApplyRadialDeadZone(Value.Get<FVector2D>(), StickDeadZone);
	if (bInvertLookY) Stick.Y *= -1.f;
	const float Scale = StickLookDegreesPerSecond * GetWorld()->GetDeltaSeconds();
	RotationInput.Yaw += Stick.X * Scale;
	RotationInput.Pitch += Stick.Y * Scale;
}

void ACarnivalPlayerController::OnContextInteract()
{
	if (auto* Char = Cast<ACarnivalPlayerCharacter>(GetPawn())) Char->TryContextInteract();
}

void ACarnivalPlayerController::OnCancel()
{
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) { Car->RequestExit(); return; }
	if (auto* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->CancelParkourTraversal();
		Char->LeaveRideOperator();
		if (Char->ActiveActivity) Char->ActiveActivity->AbortActivity();
		Char->TryRecoverToSafePosition();
	}
}

void ACarnivalPlayerController::OnStopSprint()
{
	if (!bSprintToggleMode)
	{
		if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
		{
			Char->StopSprinting();
		}
	}
}

void ACarnivalPlayerController::OnJumpVaultReleased()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn())) Char->SetSwimUpHeld(false);
}

void ACarnivalPlayerController::OnToggleCrouch()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		// In water, crouch is held to dive.
		if (Char->IsInWaterVolume()) { Char->SetSwimDownHeld(true); return; }
		Char->ToggleCrouch();
	}
}

void ACarnivalPlayerController::OnCrouchReleased()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn())) Char->SetSwimDownHeld(false);
}

void ACarnivalPlayerController::OnToggleProne()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->ToggleProne();
	}
}

void ACarnivalPlayerController::OnInteractMount()
{
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) { Car->RequestExit(); return; }
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		// Currently on bike -> dismount
		Bike->Dismount();
	}
	else if (auto* Boat = Cast<ACarnivalBoat>(GetPawn())) Boat->Dismount();
	else if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->Dismount();
	else if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		// On foot -> try mount or interact
		Char->TryInteractOrMount();
	}
}

void ACarnivalPlayerController::OnAttack()
{
	if (auto* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()); Char && (Char->IsUsingRide() || Char->IsParkourTraversing())) return;
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->BuildComponent && Char->BuildComponent->bIsBuildModeActive)
		{
			Char->BuildComponent->PlacePiece();
			return;
		}
	}

	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		// Mounted attack
		Bike->MountedShoot();
	}
	else if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->PerformAttack();
	}
}

void ACarnivalPlayerController::OnSecondary()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->IsParkourTraversing()) return;
		if (Char->BuildComponent && Char->BuildComponent->bIsBuildModeActive)
		{
			Char->BuildComponent->DemolishPiece();
		}
	}
}

void ACarnivalPlayerController::OnToggleBuild()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->IsUsingRide() || Char->IsParkourTraversing()) return;
		if (Char->BuildComponent)
		{
			Char->BuildComponent->ToggleBuildMode();
		}
	}
}

void ACarnivalPlayerController::OnRotatePiece()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->BuildComponent)
		{
			Char->BuildComponent->RotatePiece();
		}
	}
}

void ACarnivalPlayerController::OnCyclePieceNext()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->BuildComponent)
		{
			Char->BuildComponent->CyclePiece(1);
		}
	}
}

void ACarnivalPlayerController::OnCyclePiecePrev()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->BuildComponent)
		{
			Char->BuildComponent->CyclePiece(-1);
		}
	}
}

void ACarnivalPlayerController::OnCycleCategory()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (Char->BuildComponent)
		{
			Char->BuildComponent->CycleCategory(1);
		}
	}
}

void ACarnivalPlayerController::OnWeaponSlot1()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->EquipWeaponSlot(1);
	}
}

void ACarnivalPlayerController::OnWeaponSlot2()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->EquipWeaponSlot(2);
	}
}

void ACarnivalPlayerController::OnWeaponSlot3()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->EquipWeaponSlot(3);
	}
}

void ACarnivalPlayerController::OnWeaponSlot0()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->EquipWeaponSlot(0);
	}
}

void ACarnivalPlayerController::OnTravelCarnival()
{
	TravelToMap(TEXT("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"));
}

void ACarnivalPlayerController::OnTravelMansion()
{
	TravelToMap(TEXT("/Game/Mansion/Levels/LV_Haunted_Mansion"));
}

void ACarnivalPlayerController::OnTravelTown()
{
	TravelToMap(TEXT("/Game/Town/Level/L_Main_Level"));
}

void ACarnivalPlayerController::OnTravelLighthouse()
{
	TravelToMap(TEXT("/Game/LightHouse_Meshingun/Map/LV_LightHouse"));
}

void ACarnivalPlayerController::OnTravelCastle()
{
	TravelToMap(TEXT("/Game/Medieval_Castle/Level/Medieval_Castle_Level"));
}

void ACarnivalPlayerController::OnTravelArena()
{
	TravelToMap(TEXT("/Game/Gladiator_Arena/Maps/Gladiators_Land"));
}

void ACarnivalPlayerController::OnTravelMars()
{
	TravelToMap(TEXT("/Game/Mars_Futuristic_Cars/Maps/Playmap"));
}

void ACarnivalPlayerController::TravelToMap(const FString& MapName)
{
	UGameplayStatics::OpenLevel(this, FName(*MapName));
}

void ACarnivalPlayerController::OnThrottle(const FInputActionValue& Value)
{
	OtherVehicleThrottle = Value.Get<float>();
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) Car->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (auto* Boat = Cast<ACarnivalBoat>(GetPawn())) Boat->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputThrottle(Value.Get<float>());
	}
}

void ACarnivalPlayerController::OnSteer(const FInputActionValue& Value)
{
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) Car->InputSteering(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
	if (auto* Boat = Cast<ACarnivalBoat>(GetPawn())) Boat->InputSteering(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->InputSteering(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputSteering(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
	}
}

void ACarnivalPlayerController::OnBrake(const FInputActionValue& Value)
{
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) Car->InputBrake(Value.Get<float>());
	if (auto* Boat = Cast<ACarnivalBoat>(GetPawn())) Boat->InputBrake(Value.Get<float>());
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputBrake(Value.Get<float>());
	}
}

void ACarnivalPlayerController::OnHandbrake(const FInputActionValue& Value)
{
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->InputBoost(Value.Get<bool>());
	if (auto* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
		Bike->InputHandbrake(Value.Get<bool>());
}

void ACarnivalPlayerController::OnBrakeReverse(const FInputActionValue& Value)
{
	OtherVehicleReverse = Value.Get<float>();
    if (auto* Car = Cast<ACarnivalBumperCar>(GetPawn())) Car->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (auto* Boat = Cast<ACarnivalBoat>(GetPawn())) Boat->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->InputThrottle(OtherVehicleThrottle - OtherVehicleReverse);
	if (auto* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
		Bike->InputBrakeReverse(Value.Get<float>());
}

void ACarnivalPlayerController::OnRiderBalance(const FInputActionValue& Value)
{
	if (auto* Hover = Cast<ACarnivalHovercraft>(GetPawn())) Hover->InputStrafe(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
	if (auto* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
		Bike->InputRiderBalance(ApplyAxisDeadZone(Value.Get<float>(), StickDeadZone));
}

void ACarnivalPlayerController::ToggleSettingsMenu()
{
	bSettingsMenuOpen = !bSettingsMenuOpen;
	bControlRemappingOpen = false;
	bCapturingControl = false;
	if (bSettingsMenuOpen)
	{
		ClearCurrentPawnInputs(false);
		SettingsMenuSelection = FMath::Clamp(SettingsMenuSelection, 0, CarnivalInputSettingsRows - 1);
	}
	if (ACarnivalHUD* HUD = Cast<ACarnivalHUD>(GetHUD())) HUD->bShowSettingsMenu = bSettingsMenuOpen;
	SetShowMouseCursor(false);
	SetInputMode(FInputModeGameOnly());
	if (!bSettingsMenuOpen && bReturnToSessionMenu)
	{
		bReturnToSessionMenu = false;
		bSessionMenuOpen = true;
		SessionMenuSelection = 5;
	}
	FlushPressedKeys();
	SetPause(bSettingsMenuOpen || bSessionMenuOpen);
}

void ACarnivalPlayerController::SetMotorcyclePhysicsMode(EMotorcyclePhysicsMode NewMode)
{
	TArray<AActor*> FoundBikes;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ACarnivalMotorcycle::StaticClass(), FoundBikes);
	for (AActor* Actor : FoundBikes)
	{
		if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(Actor))
		{
			Bike->SetPhysicsMode(NewMode);
		}
	}
}
