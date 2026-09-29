// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalHovercraft.generated.h"

class UStaticMeshComponent;
class UBoxComponent;
class USpringArmComponent;
class UCameraComponent;
class UNiagaraComponent;
class ACarnivalPlayerCharacter;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalHovercraft : public APawn
{
	GENERATED_BODY()

public:
	ACarnivalHovercraft();

	virtual void Tick(float DeltaTime) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	virtual void UnPossessed() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* CollisionBox;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* CraftMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* MountTrigger;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USpringArmComponent* CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UCameraComponent* FollowCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UNiagaraComponent* ThrusterVFX;

	/* Hover & Propulsion Configuration */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float TargetHoverHeight = 100.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float MaxForwardSpeed = 2500.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float MaxBoostSpeed = 3800.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float MaxStrafeSpeed = 1400.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float Acceleration = 1600.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float BrakingDeceleration = 1800.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float TurnRate = 65.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float MaxBankAngle = 25.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Handling")
	float MaxPitchAngle = 15.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Seating")
	FName DriverSeatSocketName = TEXT("DriverSeat");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hover|Seating")
	FVector DriverRelativeOffset = FVector(0.0f, 0.0f, 40.0f);

	/* Runtime State */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hover|State")
	float CurrentForwardSpeed = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hover|State")
	float CurrentStrafeSpeed = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hover|State")
	float CurrentHoverHeight = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hover|State")
	bool bIsBoosting = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hover|State")
	ACarnivalPlayerCharacter* CurrentRider = nullptr;

	/* Mount / Dismount API */
	UFUNCTION(BlueprintCallable, Category = "Hover")
	bool CanMount(AActor* PotentialRider) const;

	UFUNCTION(BlueprintCallable, Category = "Hover")
	void Mount(ACarnivalPlayerCharacter* Rider);

	UFUNCTION(BlueprintCallable, Category = "Hover")
	void Dismount();

	/* Controls */
	UFUNCTION(BlueprintCallable, Category = "Hover|Input")
	void InputThrottle(float Value);

	UFUNCTION(BlueprintCallable, Category = "Hover|Input")
	void InputSteering(float Value);

	UFUNCTION(BlueprintCallable, Category = "Hover|Input")
	void InputStrafe(float Value);

	UFUNCTION(BlueprintCallable, Category = "Hover|Input")
	void InputBoost(bool bEnable);

	UFUNCTION(BlueprintCallable, Category = "Hover|Input")
	void ClearControlInputs();

protected:
	virtual void BeginPlay() override;

	void UpdateHoverPhysics(float DeltaTime);
	void RestoreRider(bool bEmergency);
	void RecoverLostPossession();
	FTransform BoardingTransform;
	TWeakObjectPtr<AController> BoardingController;
	float FallVelocity = 0.f;

	float ThrottleInput = 0.0f;
	float SteeringInput = 0.0f;
	float StrafeInput = 0.0f;
	float CurrentBank = 0.0f;
	float CurrentPitch = 0.0f;
};
