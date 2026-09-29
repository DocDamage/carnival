// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalPlayerCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UAnimMontage;
class UAnimSequence;
class ACarnivalMotorcycle;
class ACarnivalBoat;
class ACarnivalHovercraft;
class ACarnivalWeaponBase;
class UCarnivalBuildComponent;
class ACarnivalActivityBase;
class ACarnivalMissionInteractionActor;
class ACarnivalRideAttendant;
class UCarnivalRidePassengerComponent;
class UCarnivalRideOperationComponent;
class UCarnivalRideSeatComponent;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalPlayerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ACarnivalPlayerCharacter();

	virtual void Tick(float DeltaTime) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	virtual void Landed(const FHitResult& Hit) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	USpringArmComponent* CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	UCameraComponent* FollowCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build")
	UCarnivalBuildComponent* BuildComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Rides")
    TObjectPtr<UCarnivalRidePassengerComponent> RidePassenger;
    UPROPERTY(BlueprintReadOnly, Category="Rides")
    TObjectPtr<UCarnivalRideOperationComponent> OperatingRide;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Rides")
    TObjectPtr<UAnimSequence> RideSeatedAnimation;
    UFUNCTION(BlueprintPure, Category="Rides")
    ACarnivalRideAttendant* FindNearbyAttendant() const;
    UFUNCTION(BlueprintCallable, Category="Rides")
    void InteractWithRideOperator();
    UFUNCTION(BlueprintCallable, Category="Rides")
    void LeaveRideOperator();
    UFUNCTION(BlueprintPure, Category="Rides")
    bool IsUsingRide() const;

	/* Current locomotion state */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Locomotion")
	ECarnivalLocomotionState LocomotionState;

	/* Speeds */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float WalkSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float JogSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float SprintSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float CrouchSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float ProneSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Speeds")
	float SwimSpeed;

	/* Fall & Roll Settings */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Roll")
	float RollLandingVelocityThreshold;

	/* Parkour Tracing */
	UFUNCTION(BlueprintCallable, Category = "Locomotion|Parkour")
	bool TryVaultOrMantle();

	UFUNCTION(BlueprintCallable, Category = "Locomotion|Parkour")
	bool TryLadderClimb();

	UFUNCTION(BlueprintPure, Category = "Locomotion|Parkour")
	bool IsParkourTraversing() const { return ParkourPath.Num() > 0; }

	UFUNCTION(BlueprintCallable, Category = "Locomotion|Parkour")
	void CancelParkourTraversal();

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Locomotion|Parkour", meta = (ClampMin = "50"))
	float ParkourTraversalSpeed = 260.f;

	/* Locomotion Controls */
	UFUNCTION(BlueprintCallable, Category = "Locomotion")
	void SetLocomotionState(ECarnivalLocomotionState NewState);

	UFUNCTION(BlueprintCallable, Category = "Locomotion")
	void StartSprinting();

	UFUNCTION(BlueprintCallable, Category = "Locomotion")
	void StopSprinting();

	UFUNCTION(BlueprintCallable, Category = "Locomotion")
	void ToggleCrouch();

	UFUNCTION(BlueprintCallable, Category = "Locomotion")
	void ToggleProne();

	/* Vehicle Integration */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Vehicle")
	ACarnivalMotorcycle* MountedMotorcycle;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Vehicle")
	ACarnivalBoat* MountedBoat;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Vehicle")
	ACarnivalHovercraft* MountedHovercraft;

	/* Activity Integration */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity")
	ACarnivalActivityBase* ActiveActivity;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity")
	ACarnivalActivityBase* NearbyActivity;

	UFUNCTION(BlueprintCallable, Category = "Vehicle")
	void TryInteractOrMount();

	UFUNCTION(BlueprintCallable, Category = "Interaction")
	void TryContextInteract();

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	ACarnivalMissionInteractionActor* FindNearbyMissionInteraction() const;

	UFUNCTION(BlueprintPure, Category = "Recovery")
	bool CanRecoverToSafePosition() const;

	UFUNCTION(BlueprintCallable, Category = "Recovery")
	bool TryRecoverToSafePosition();

	void OnMountMotorcycle(ACarnivalMotorcycle* Bike, bool bMountLeft);
	void OnDismountMotorcycle(ACarnivalMotorcycle* Bike, bool bDismountLeft = true);
	void PerformMountedAttack(bool bIsShooting, bool bPunchRight = false);

	void OnMountBoat(ACarnivalBoat* Boat);
	void OnDismountBoat();

	void OnMountHovercraft(ACarnivalHovercraft* Craft);
	void OnDismountHovercraft();

	/* Weapon & Combat */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Combat")
	ACarnivalWeaponBase* CurrentWeapon;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat")
	TSubclassOf<ACarnivalWeaponBase> DefaultSwordClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat")
	TSubclassOf<ACarnivalWeaponBase> DefaultRevolverClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat")
	TSubclassOf<ACarnivalWeaponBase> DefaultKnifeClass;

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void EquipWeaponSlot(int32 SlotIndex);

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void PerformAttack();

	/* Montages for locomotion actions */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* VaultMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* Mantle1MMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* Mantle2MMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* LandingRollMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* StandToProneMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* ProneToStandMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* MountLeftMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* MountRightMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* DismountLeftMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* DismountRightMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* RidingIdleMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* MountedPunchLeftMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* MountedPunchRightMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* MountedShootMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* UnarmedPunchMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Animations|Montages")
	UAnimMontage* UnarmedKickMontage;

	/* Input Actions */
	void MoveForward(float Value);
	void MoveRight(float Value);
	void TurnAtRate(float Rate);
	void LookUpAtRate(float Rate);

protected:
	virtual void BeginPlay() override;
    UFUNCTION()
    void HandleRideBoarded(AActor* RideActor, UCarnivalRideSeatComponent* Seat);
    UFUNCTION()
    void HandleRideUnboarded(AActor* RideActor);
    float PreRideCameraLength = 350.f;
    uint8 PreRideAnimationMode = 0;
    UPROPERTY(Transient)
    TObjectPtr<UClass> PreRideAnimClass;

	float DefaultCapsuleHalfHeight;
	float DefaultCapsuleRadius;
	bool bIsProne;

	UPROPERTY(EditDefaultsOnly, Category = "Recovery", meta = (ClampMin = "0.1"))
	float BlockedInputRecoveryDelay = 4.f;
	UPROPERTY(EditDefaultsOnly, Category = "Recovery", meta = (ClampMin = "0.1"))
	float SwimmingRecoveryDelay = 4.f;
	UPROPERTY(EditDefaultsOnly, Category = "Recovery", meta = (ClampMin = "0.1"))
	float FallingRecoveryDelay = 5.f;

	FVector LastSafeRecoveryLocation = FVector::ZeroVector;
	FRotator LastSafeRecoveryRotation = FRotator::ZeroRotator;
	float SafeLocationRefreshTime = 0.f;
	float BlockedInputDuration = 0.f;
	float SwimmingDuration = 0.f;
	float FallingDuration = 0.f;
	bool bHasSafeRecoveryLocation = false;

	void UpdateSafeRecoveryState(float DeltaTime);
	bool FindSafeRecoveryLocation(FVector& OutLocation) const;

	bool BeginParkourTraversal(const TArray<FVector>& Path, ECarnivalLocomotionState State, UAnimMontage* Montage);
	void UpdateParkourTraversal(float DeltaTime);
	TArray<FVector> ParkourPath;
	int32 ParkourPointIndex = 0;
	double NextUnarmedAttackTime = 0.0;
	bool bPunchNext = true;
};
