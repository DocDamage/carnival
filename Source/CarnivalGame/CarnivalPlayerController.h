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
	virtual bool InputKey(const FInputKeyEventArgs& Params) override;

	UPROPERTY(BlueprintReadOnly, Category = "Input")
	bool bUsingGamepad = false;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input")
	bool bControllerDisconnectPaused = false;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input")
	bool bSettingsMenuOpen = false;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input|Settings")
	bool bInvertLookY = false;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input|Settings")
	float StickDeadZone = 0.12f;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input|Settings")
	bool bSprintToggleMode = false;

	UPROPERTY(BlueprintReadOnly, Transient, Category = "Input|Settings")
	int32 SettingsMenuSelection = 0;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Input")
	bool bPlayStationPrompts = true;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Input")
	float StickLookDegreesPerSecond = 120.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* LookStickAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* ContextInteractAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	UInputAction* CancelAction;

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

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Input")
	UInputAction* BrakeReverseAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Motorcycle")
	UInputAction* HandbrakeAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Motorcycle")
	UInputAction* RiderBalanceAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UUserWidget> SettingsMenuWidgetClass;

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ToggleSettingsMenu();

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void OpenControlRemapping(bool bGamepad = false);

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SetMotorcyclePhysicsMode(EMotorcyclePhysicsMode NewMode);

	UFUNCTION(BlueprintCallable, Category = "Travel")
	void TravelToMap(const FString& MapName);

	// Runtime copies retain authored modifiers; source input assets are never edited.
	void InitializeControlRemapping();
	bool RemapControl(int32 BindingIndex, FKey NewKey);
	void RestoreControlDefaults();
	FString GetActionKeyLabel(const UInputAction* Action) const;
	TArray<FString> GetControlRemappingLines() const;
	bool bControlRemappingOpen = false;
	bool bCapturingControl = false;
	bool bRemapGamepad = false;
	int32 ControlRemappingSelection = 0;
	FString ControlRemappingFeedback;
	struct FControlBinding
	{
		UInputMappingContext* Context = nullptr;
		int32 MappingIndex = 0;
		FKey DefaultKey;
		FString SaveId;
		FString Label;
	};
	TArray<FControlBinding> ControlBindings;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void SetupInputComponent() override;
	virtual void OnPossess(APawn* InPawn) override;
	virtual void OnUnPossess() override;

	UFUNCTION()
	void HandleInputDeviceConnectionChange(EInputDeviceConnectionState NewConnectionState, FPlatformUserId PlatformUserId, FInputDeviceId InputDeviceId);

	void ClearCurrentPawnInputs(bool bLeaveRideOperator = true);
	void LoadPlayerInputSettings();
	void SavePlayerInputSettings() const;
	void HandleSettingsMenuInput(const FInputKeyEventArgs& Params);
	void AdjustSelectedSetting(int32 Direction);
	void ActivateSelectedSetting();
	void ResetPlayerInputSettings();
	void HandleControlRemappingInput(const FInputKeyEventArgs& Params);
	void RebuildControlMappings();
	void SaveControlRemapping() const;
	TArray<int32> GetVisibleControlBindings() const;
	FString GetKeyLabel(FKey Key) const;
	bool bControlMappingsInitialized = false;

	void OnMove(const FInputActionValue& Value);
	void OnLook(const FInputActionValue& Value);
	void OnLookStick(const FInputActionValue& Value);
	void OnContextInteract();
	void OnCancel();
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
	void OnBrakeReverse(const FInputActionValue& Value);
	void OnHandbrake(const FInputActionValue& Value);
	void OnRiderBalance(const FInputActionValue& Value);

	UPROPERTY()
	UUserWidget* SettingsMenuWidget;

	FInputDeviceId LastActiveGamepadDeviceId = INPUTDEVICEID_NONE;
	bool bSprintToggleActive = false;
	float OtherVehicleThrottle = 0.f;
	float OtherVehicleReverse = 0.f;
};
