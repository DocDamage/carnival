// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalPlayerController.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBuildComponent.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"

ACarnivalPlayerController::ACarnivalPlayerController()
{
	SettingsMenuWidget = nullptr;
}

void ACarnivalPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (DefaultMappingContext)
		{
			Subsystem->AddMappingContext(DefaultMappingContext, 0);
		}
	}
}

void ACarnivalPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (InPawn && InPawn->IsA<ACarnivalMotorcycle>())
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
		if (JumpVaultAction)
		{
			EnhancedInputComponent->BindAction(JumpVaultAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnJumpVault);
		}
		if (SprintAction)
		{
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnStartSprint);
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Completed, this, &ACarnivalPlayerController::OnStopSprint);
		}
		if (CrouchAction)
		{
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnToggleCrouch);
		}
		if (ProneAction)
		{
			EnhancedInputComponent->BindAction(ProneAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnToggleProne);
		}
		if (InteractMountAction)
		{
			EnhancedInputComponent->BindAction(InteractMountAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::OnInteractMount);
		}
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

		// Settings Menu
		if (SettingsMenuAction)
		{
			EnhancedInputComponent->BindAction(SettingsMenuAction, ETriggerEvent::Started, this, &ACarnivalPlayerController::ToggleSettingsMenu);
		}

		// Fast Travel Hotkeys (F1-F7)
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

		// Motorcycle driving
		if (ThrottleAction)
		{
			EnhancedInputComponent->BindAction(ThrottleAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnThrottle);
		}
		if (SteerAction)
		{
			EnhancedInputComponent->BindAction(SteerAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnSteer);
		}
		if (BrakeAction)
		{
			EnhancedInputComponent->BindAction(BrakeAction, ETriggerEvent::Triggered, this, &ACarnivalPlayerController::OnBrake);
		}
	}
}

void ACarnivalPlayerController::OnMove(const FInputActionValue& Value)
{
	FVector2D MovementVector = Value.Get<FVector2D>();
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
	AddPitchInput(LookVector.Y);
}

void ACarnivalPlayerController::OnJumpVault()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		if (!Char->TryVaultOrMantle())
		{
			Char->Jump();
		}
	}
}

void ACarnivalPlayerController::OnStartSprint()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->StartSprinting();
	}
}

void ACarnivalPlayerController::OnStopSprint()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->StopSprinting();
	}
}

void ACarnivalPlayerController::OnToggleCrouch()
{
	if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		Char->ToggleCrouch();
	}
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
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		// Currently on bike -> dismount
		Bike->Dismount();
	}
	else if (ACarnivalPlayerCharacter* Char = Cast<ACarnivalPlayerCharacter>(GetPawn()))
	{
		// On foot -> try mount or interact
		Char->TryInteractOrMount();
	}
}

void ACarnivalPlayerController::OnAttack()
{
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
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputThrottle(Value.Get<float>());
	}
}

void ACarnivalPlayerController::OnSteer(const FInputActionValue& Value)
{
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputSteering(Value.Get<float>());
	}
}

void ACarnivalPlayerController::OnBrake(const FInputActionValue& Value)
{
	if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(GetPawn()))
	{
		Bike->InputBrake(Value.Get<float>());
	}
}

void ACarnivalPlayerController::ToggleSettingsMenu()
{
	if (SettingsMenuWidget && SettingsMenuWidget->IsInViewport())
	{
		SettingsMenuWidget->RemoveFromParent();
		SetShowMouseCursor(false);
		SetInputMode(FInputModeGameOnly());
	}
	else if (SettingsMenuWidgetClass)
	{
		if (!SettingsMenuWidget)
		{
			SettingsMenuWidget = CreateWidget<UUserWidget>(this, SettingsMenuWidgetClass);
		}
		if (SettingsMenuWidget)
		{
			SettingsMenuWidget->AddToViewport(100);
			SetShowMouseCursor(true);
			FInputModeGameAndUI InputMode;
			InputMode.SetWidgetToFocus(SettingsMenuWidget->TakeWidget());
			SetInputMode(InputMode);
		}
	}
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

