// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalPlayerCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UAnimMontage;
class ACarnivalMotorcycle;
class ACarnivalBoat;
class ACarnivalHovercraft;
class ACarnivalWeaponBase;
class UCarnivalBuildComponent;
class ACarnivalActivityBase;

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

	void OnMountMotorcycle(ACarnivalMotorcycle* Bike, bool bMountLeft);
	void OnDismountMotorcycle(ACarnivalMotorcycle* Bike);
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

	float DefaultCapsuleHalfHeight;
	float DefaultCapsuleRadius;
	bool bIsProne;
};

