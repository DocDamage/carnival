// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalMotorcycle.generated.h"

class USkeletalMeshComponent;
class UStaticMeshComponent;
class UBoxComponent;
class USpringArmComponent;
class UCameraComponent;
class UNiagaraComponent;
class UAnimMontage;
class AController;
class ACarnivalPlayerCharacter;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalMotorcycle : public APawn
{
	GENERATED_BODY()

public:
	ACarnivalMotorcycle();

	virtual void Tick(float DeltaTime) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	virtual void UnPossessed() override;
	virtual void Destroyed() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USkeletalMeshComponent* BikeMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* FrontWheel;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* RearWheel;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float WheelRadius = 43.746f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float MaxStepHeight = 35.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* MountTriggerLeft;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* MountTriggerRight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USpringArmComponent* CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UCameraComponent* FollowCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UNiagaraComponent* ExhaustVFX;

	/* Physics simulation mode: Arcade (default, responsive, no tipping) vs ChaosPhysics */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Motorcycle|Settings")
	EMotorcyclePhysicsMode PhysicsMode;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Sockets")
	FName DriverSeatSocketName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Mount", meta=(ClampMin="0.0"))
	float MountApproachRadius = 75.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Recovery", meta=(ClampMin="0.1"))
	float StuckRecoveryDelay = 1.25f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float MaxSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float ReverseSpeed;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float Acceleration;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float BrakingDeceleration;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float TurnRate;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float MaxLeanAngle;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float MaxWheelieAngle = 32.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motorcycle|Handling")
	float AirPitchRate = 65.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	float WheelieAngle = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	float SlipAngle = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	float CurrentSpeed;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	float CurrentLean;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	float VerticalVelocity;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	bool bIsAirborne;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Motorcycle|State")
	ACarnivalPlayerCharacter* CurrentRider;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Motorcycle|Diagnostics")
	FHitResult LastMovementHit;

	/* Mount / Dismount API */
	UFUNCTION(BlueprintCallable, Category = "Motorcycle")
	bool CanMount(AActor* PotentialRider, bool& bOutMountLeft) const;

	UFUNCTION(BlueprintCallable, Category = "Motorcycle")
	void Mount(ACarnivalPlayerCharacter* Rider, bool bMountLeft);

	UFUNCTION(BlueprintCallable, Category = "Motorcycle")
	void Dismount();

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Recovery")
	bool CanRecoverFromStuckOrOverturned() const;

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Recovery")
	bool TryRecoverFromStuckOrOverturned();

	void ResetForStoryMissionRetry(const FTransform& StartTransform, EMotorcyclePhysicsMode StartPhysicsMode);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category="Motorcycle|State")
	bool bDismounting = false;

	/* In-game settings toggle */
	UFUNCTION(BlueprintCallable, Category = "Motorcycle")
	void SetPhysicsMode(EMotorcyclePhysicsMode NewMode);

	/* Mounted Combat */
	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Combat")
	void MountedShoot();

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Combat")
	void MountedPunch(bool bPunchRight);

	/* Driving Inputs */
	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Input")
	void InputThrottle(float Value);

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Input")
	void InputSteering(float Value);

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Input")
	void InputBrake(float Value);

	UFUNCTION(BlueprintCallable, Category="Motorcycle|Input")
	void InputBrakeReverse(float Value);

	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Input")
	void InputHandbrake(bool bPressed);

	// Positive input pulls the rider back; negative input leans forward.
	UFUNCTION(BlueprintCallable, Category = "Motorcycle|Input")
	void InputRiderBalance(float Value);

protected:
	virtual void BeginPlay() override;

	void UpdateArcadePhysics(float DeltaTime);
	void UpdateChaosPhysics(float DeltaTime);
	bool GetMountApproachTransform(bool bMountLeft, FVector& OutLocation, FRotator& OutRotation) const;
	bool IsMountApproachClear(ACarnivalPlayerCharacter* Rider, FVector ApproachLocation, FRotator ApproachRotation) const;
	bool AlignRiderForMount(ACarnivalPlayerCharacter* Rider, bool bMountLeft) const;
	bool FindDismountLocation(FVector& Location, bool& bLeft) const;
	void UpdateDismount();
	void CompleteDismount();
	void HandleLostPossessionRecovery();
	void RecoverMountedRider(bool bRestorePossession);
	FVector DismountStart;
	FVector DismountDestination;
	float LastDismountMontagePosition = 0.f;
	bool bDismountLeft = true;
	UPROPERTY(Transient)
	UAnimMontage* ActiveDismountMontage = nullptr;
	UPROPERTY(Transient)
	AController* MountingController = nullptr;

	float ThrottleInput;
	float SteeringInput;
	float BrakeInput;
	float BrakeReverseInput = 0.f;
	bool bHandbrake;
	float RiderBalanceInput = 0.f;
	float TravelYaw = 0.f;
	bool bHasTravelHeading = false;
	float WheelSpinDegrees = 0.f;
	float BlockedDriveDuration = 0.f;
	FVector LastGroundNormal = FVector::UpVector;
};
