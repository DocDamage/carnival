// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalBoat.generated.h"

class UStaticMeshComponent;
class UBoxComponent;
class USpringArmComponent;
class UCameraComponent;
class ACarnivalPlayerCharacter;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalBoat : public APawn
{
	GENERATED_BODY()

public:
	ACarnivalBoat();

	virtual void Tick(float DeltaTime) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	virtual void UnPossessed() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* CollisionBox;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* BoatMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* PropellerMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* MountTrigger;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USpringArmComponent* CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UCameraComponent* FollowCamera;

	/* Handling Configuration */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float MaxForwardSpeed = 2200.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float MaxReverseSpeed = 800.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float Acceleration = 1200.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float BrakingDeceleration = 1500.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float TurnRate = 50.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Handling")
	float MaxBankAngle = 15.0f;

	/* Water & Buoyancy Simulation */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water")
	float WaterPlaneZ = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water")
	bool bAutoDetectWater = true;

	/** Explicit surveyed world-space region. Disabled for legacy placements. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water|Boundary")
	bool bUseNavigableWaterBounds = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water|Boundary", meta = (EditCondition = "bUseNavigableWaterBounds"))
	FVector2D NavigableWaterMin = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water|Boundary", meta = (EditCondition = "bUseNavigableWaterBounds"))
	FVector2D NavigableWaterMax = FVector2D::ZeroVector;

	/** Reject solid ground above the bottom of the hull plus this clearance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water|Boundary", meta = (ClampMin = "0", EditCondition = "bUseNavigableWaterBounds"))
	float MinimumKeelClearance = 25.f;

	UFUNCTION(BlueprintPure, Category = "Boat|Water")
	bool IsWaterTransformNavigable(FVector Location, FRotator Rotation) const;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water")
	float WaveBobAmplitude = 12.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boat|Water")
	float WaveBobFrequency = 1.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Boat|Seating")
	FName DriverSeatSocketName = TEXT("DriverSeat");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Boat|Seating")
	FVector DriverRelativeOffset = FVector(-30.0f, 0.0f, 40.0f);

	/* Runtime State */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Boat|State")
	float CurrentSpeed = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Boat|State")
	float CurrentBank = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Boat|State")
	float CurrentPitch = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Boat|State")
	ACarnivalPlayerCharacter* CurrentRider = nullptr;

	/* Mount / Dismount API */
	UFUNCTION(BlueprintCallable, Category = "Boat")
	bool CanMount(AActor* PotentialRider) const;

	UFUNCTION(BlueprintCallable, Category = "Boat")
	void Mount(ACarnivalPlayerCharacter* Rider);

	UFUNCTION(BlueprintCallable, Category = "Boat")
	void Dismount();

	/* Controls */
	UFUNCTION(BlueprintCallable, Category = "Boat|Input")
	void InputThrottle(float Value);

	UFUNCTION(BlueprintCallable, Category = "Boat|Input")
	void InputSteering(float Value);

	UFUNCTION(BlueprintCallable, Category = "Boat|Input")
	void InputBrake(float Value);

	UFUNCTION(BlueprintCallable, Category = "Boat|Input")
	void ClearControlInputs();

protected:
	virtual void BeginPlay() override;

	void UpdateWaterPhysics(float DeltaTime);
	void RestoreRider(bool bEmergency);
	void RecoverLostPossession();
	FTransform BoardingTransform;
	TWeakObjectPtr<AController> BoardingController;

	float ThrottleInput = 0.0f;
	float SteeringInput = 0.0f;
	float BrakeInput = 0.0f;
	float WaveTime = 0.0f;
	float TargetWaterZ = 0.0f;
};
