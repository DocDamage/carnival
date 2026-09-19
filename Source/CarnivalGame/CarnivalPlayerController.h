// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalPlayerController.generated.h"

class UInputMappingContext;
class UInputAction;
struct FInputActionValue;
class UUserWidget;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ACarnivalPlayerController();

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputMappingContext* DefaultMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputMappingContext* MotorcycleMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* MoveAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* JumpVaultAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* SprintAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* CrouchAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* ProneAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* InteractMountAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* AttackAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* SecondaryAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Build")
	UInputAction* ToggleBuildAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Build")
	UInputAction* RotatePieceAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Build")
	UInputAction* CyclePieceNextAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Build")
	UInputAction* CyclePiecePrevAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Build")
	UInputAction* CycleCategoryAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* WeaponSlot1Action;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* WeaponSlot2Action;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* WeaponSlot3Action;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* WeaponSlot0Action;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* SettingsMenuAction;

	/* Fast-Travel Hotkeys (F1-F7) */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelCarnivalAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelMansionAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelTownAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelLighthouseAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelCastleAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelArenaAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Travel")
	UInputAction* TravelMarsAction;

	/* Motorcycle Specific Actions */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Motorcycle")
	UInputAction* ThrottleAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Motorcycle")
	UInputAction* SteerAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Motorcycle")
	UInputAction* BrakeAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UUserWidget> SettingsMenuWidgetClass;

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ToggleSettingsMenu();

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SetMotorcyclePhysicsMode(EMotorcyclePhysicsMode NewMode);

	UFUNCTION(BlueprintCallable, Category = "Travel")
	void TravelToMap(const FString& MapName);

protected:
	virtual void BeginPlay() override;
	virtual void SetupInputComponent() override;
	virtual void OnPossess(APawn* InPawn) override;

	void OnMove(const FInputActionValue& Value);
	void OnLook(const FInputActionValue& Value);
	void OnJumpVault();
	void OnStartSprint();
	void OnStopSprint();
	void OnToggleCrouch();
	void OnToggleProne();
	void OnInteractMount();
	void OnAttack();
	void OnSecondary();
	void OnToggleBuild();
	void OnRotatePiece();
	void OnCyclePieceNext();
	void OnCyclePiecePrev();
	void OnCycleCategory();
	void OnWeaponSlot1();
	void OnWeaponSlot2();
	void OnWeaponSlot3();
	void OnWeaponSlot0();

	void OnTravelCarnival();
	void OnTravelMansion();
	void OnTravelTown();
	void OnTravelLighthouse();
	void OnTravelCastle();
	void OnTravelArena();
	void OnTravelMars();

	void OnThrottle(const FInputActionValue& Value);
	void OnSteer(const FInputActionValue& Value);
	void OnBrake(const FInputActionValue& Value);

	UPROPERTY()
	UUserWidget* SettingsMenuWidget;
};

