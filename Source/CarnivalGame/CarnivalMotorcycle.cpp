// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalMotorcycle.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "NiagaraComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "DrawDebugHelpers.h"

ACarnivalMotorcycle::ACarnivalMotorcycle()
{
	PrimaryActorTick.bCanEverTick = true;

	BikeMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("BikeMesh"));
	SetRootComponent(BikeMesh);
	BikeMesh->SetCollisionProfileName(TEXT("Vehicle"));

	MountTriggerLeft = CreateDefaultSubobject<UBoxComponent>(TEXT("MountTriggerLeft"));
	MountTriggerLeft->SetupAttachment(BikeMesh);
	MountTriggerLeft->SetBoxExtent(FVector(60.0f, 40.0f, 60.0f));
	MountTriggerLeft->SetRelativeLocation(FVector(0.0f, -60.0f, 50.0f));
	MountTriggerLeft->SetCollisionResponseToAllChannels(ECR_Ignore);
	MountTriggerLeft->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

	MountTriggerRight = CreateDefaultSubobject<UBoxComponent>(TEXT("MountTriggerRight"));
	MountTriggerRight->SetupAttachment(BikeMesh);
	MountTriggerRight->SetBoxExtent(FVector(60.0f, 40.0f, 60.0f));
	MountTriggerRight->SetRelativeLocation(FVector(0.0f, 60.0f, 50.0f));
	MountTriggerRight->SetCollisionResponseToAllChannels(ECR_Ignore);
	MountTriggerRight->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(BikeMesh);
	CameraBoom->TargetArmLength = 350.0f;
	CameraBoom->SetRelativeLocation(FVector(0.0f, 0.0f, 100.0f));
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bInheritPitch = true;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bInheritRoll = false;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	ExhaustVFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("ExhaustVFX"));
	ExhaustVFX->SetupAttachment(BikeMesh);
	ExhaustVFX->SetRelativeLocation(FVector(-80.0f, 15.0f, 30.0f));
	ExhaustVFX->bAutoActivate = true;

	PhysicsMode = EMotorcyclePhysicsMode::Arcade;
	DriverSeatSocketName = TEXT("DriverSeat");
	MaxSpeed = 2200.0f;
	ReverseSpeed = 500.0f;
	Acceleration = 1200.0f;
	BrakingDeceleration = 1800.0f;
	TurnRate = 75.0f;
	MaxLeanAngle = 28.0f;

	CurrentSpeed = 0.0f;
	CurrentLean = 0.0f;
	CurrentRider = nullptr;

	ThrottleInput = 0.0f;
	SteeringInput = 0.0f;
	BrakeInput = 0.0f;
	bHandbrake = false;
}

void ACarnivalMotorcycle::BeginPlay()
{
	Super::BeginPlay();
}

void ACarnivalMotorcycle::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (PhysicsMode == EMotorcyclePhysicsMode::Arcade)
	{
		UpdateArcadePhysics(DeltaTime);
	}
	else
	{
		UpdateChaosPhysics(DeltaTime);
	}
}

void ACarnivalMotorcycle::UpdateArcadePhysics(float DeltaTime)
{
	// Acceleration and Braking
	if (ThrottleInput > 0.01f)
	{
		CurrentSpeed = FMath::FInterpTo(CurrentSpeed, MaxSpeed * ThrottleInput, DeltaTime, 2.0f);
	}
	else if (ThrottleInput < -0.01f)
	{
		CurrentSpeed = FMath::FInterpTo(CurrentSpeed, -ReverseSpeed * FMath::Abs(ThrottleInput), DeltaTime, 3.0f);
	}
	else
	{
		// Coasting friction
		float DecelRate = (BrakeInput > 0.1f || bHandbrake) ? BrakingDeceleration : 400.0f;
		CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, 0.0f, DeltaTime, DecelRate);
	}

	// Steering and Yaw rotation
	float SpeedRatio = FMath::Clamp(FMath::Abs(CurrentSpeed) / MaxSpeed, 0.0f, 1.0f);
	if (FMath::Abs(CurrentSpeed) > 10.0f)
	{
		float DirectionMultiplier = (CurrentSpeed >= 0.0f) ? 1.0f : -1.0f;
		float YawDelta = SteeringInput * TurnRate * DirectionMultiplier * DeltaTime * FMath::Clamp(SpeedRatio + 0.2f, 0.2f, 1.0f);
		AddActorWorldRotation(FRotator(0.0f, YawDelta, 0.0f));
	}

	// Dynamic Leaning
	float TargetLean = -SteeringInput * MaxLeanAngle * SpeedRatio;
	CurrentLean = FMath::FInterpTo(CurrentLean, TargetLean, DeltaTime, 6.0f);

	// Forward movement
	FVector ForwardMove = GetActorForwardVector() * CurrentSpeed * DeltaTime;
	FHitResult SweepHit;
	AddActorWorldOffset(ForwardMove, true, &SweepHit);

	// Ground alignment raycast
	FVector StartTrace = GetActorLocation() + FVector(0.0f, 0.0f, 50.0f);
	FVector EndTrace = GetActorLocation() - FVector(0.0f, 0.0f, 120.0f);
	FHitResult GroundHit;
	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);
	if (CurrentRider)
	{
		Params.AddIgnoredActor(CurrentRider);
	}

	if (GetWorld()->LineTraceSingleByChannel(GroundHit, StartTrace, EndTrace, ECC_WorldStatic, Params))
	bool bHit = GetWorld()->LineTraceSingleByChannel(GroundHit, StartTrace, EndTrace, ECC_WorldStatic, Params);
	if (bHit && VerticalVelocity <= 0.0f)
	{
		// Smoothly position onto ground
		float TargetZ = GroundHit.ImpactPoint.Z;
		FVector NewLoc = GetActorLocation();
		NewLoc.Z = FMath::FInterpTo(NewLoc.Z, TargetZ, DeltaTime, 12.0f);
		SetActorLocation(NewLoc);

		// Align roll with leaning and pitch with ground slope
		FRotator CurrentRot = GetActorRotation();
		FVector Normal = GroundHit.ImpactNormal;
		FRotator SlopeRot = Normal.ToOrientationRotator();
		float TargetPitch = SlopeRot.Pitch + 90.0f;
		

		// Launch off ramp if speeding off an upward slope
		if (bIsAirborne == false && TargetPitch > 8.0f && CurrentSpeed > 350.0f)
		{
			FVector FrontStart = GetActorLocation() + GetActorForwardVector() * 160.0f + FVector(0.0f, 0.0f, 50.0f);
			FVector FrontEnd = FrontStart - FVector(0.0f, 0.0f, 150.0f);
			FHitResult FrontHit;
			if (!GetWorld()->LineTraceSingleByChannel(FrontHit, FrontStart, FrontEnd, ECC_WorldStatic, Params))
			{
				bIsAirborne = true;
				VerticalVelocity = CurrentSpeed * FMath::Sin(FMath::DegreesToRadians(TargetPitch)) * 1.3f;
			}
		}

		bIsAirborne = false;
		VerticalVelocity = 0.0f;

		FRotator TargetRot(TargetPitch, CurrentRot.Yaw, CurrentLean);
		SetActorRotation(FMath::RInterpTo(CurrentRot, TargetRot, DeltaTime, 8.0f));
	}
	else
	{
		// In the air (ballistic jump!)
		bIsAirborne = true;
		VerticalVelocity -= 980.0f * DeltaTime; // Gravity
		FVector NewLoc = GetActorLocation();
		NewLoc.Z += VerticalVelocity * DeltaTime;
		SetActorLocation(NewLoc);

		// Orient towards flight path
		FRotator CurrentRot = GetActorRotation();
		float FlightPitch = FMath::Clamp(VerticalVelocity * 0.03f, -35.0f, 35.0f);
		FRotator TargetRot(FlightPitch, CurrentRot.Yaw, CurrentLean * 0.5f);
		SetActorRotation(FMath::RInterpTo(CurrentRot, TargetRot, DeltaTime, 4.0f));
	}
}

void ACarnivalMotorcycle::UpdateChaosPhysics(float DeltaTime)
{
	// Physics-driven fallback using forces
	if (BikeMesh && BikeMesh->IsSimulatingPhysics())
	{
		if (FMath::Abs(ThrottleInput) > 0.01f)
		{
			FVector Force = GetActorForwardVector() * ThrottleInput * Acceleration * 250.0f;
			BikeMesh->AddForce(Force);
		}
		if (FMath::Abs(SteeringInput) > 0.01f)
		{
			FVector Torque = FVector(0.0f, 0.0f, SteeringInput * TurnRate * 5000.0f);
			BikeMesh->AddTorqueInDegrees(Torque);
		}
		CurrentSpeed = FVector::DotProduct(GetVelocity(), GetActorForwardVector());
	}
}

void ACarnivalMotorcycle::SetPhysicsMode(EMotorcyclePhysicsMode NewMode)
{
	PhysicsMode = NewMode;
	if (BikeMesh)
	{
		if (PhysicsMode == EMotorcyclePhysicsMode::ChaosPhysics)
		{
			BikeMesh->SetSimulatePhysics(true);
		}
		else
		{
			BikeMesh->SetSimulatePhysics(false);
		}
	}
}

bool ACarnivalMotorcycle::CanMount(AActor* PotentialRider, bool& bOutMountLeft) const
{
	if (CurrentRider != nullptr || !PotentialRider)
	{
		return false;
	}

	FVector RiderLoc = PotentialRider->GetActorLocation();
	float DistLeft = FVector::DistSquared(RiderLoc, MountTriggerLeft->GetComponentLocation());
	float DistRight = FVector::DistSquared(RiderLoc, MountTriggerRight->GetComponentLocation());

	bOutMountLeft = (DistLeft <= DistRight);
	return (DistLeft <= 25000.0f || DistRight <= 25000.0f); // within ~150cm
}

void ACarnivalMotorcycle::Mount(ACarnivalPlayerCharacter* Rider, bool bMountLeft)
{
	if (!Rider || CurrentRider != nullptr)
	{
		return;
	}

	CurrentRider = Rider;
	CurrentRider->OnMountMotorcycle(this, bMountLeft);

	APlayerController* PC = Cast<APlayerController>(Rider->GetController());
	if (PC)
	{
		PC->Possess(this);
	}
}

void ACarnivalMotorcycle::Dismount()
{
	if (!CurrentRider)
	{
		return;
	}

	ACarnivalPlayerCharacter* RiderToRestore = CurrentRider;
	CurrentRider = nullptr;

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (PC && RiderToRestore)
	{
		PC->Possess(RiderToRestore);
	}

	RiderToRestore->OnDismountMotorcycle(this);
}

void ACarnivalMotorcycle::MountedShoot()
{
	if (CurrentRider)
	{
		CurrentRider->PerformMountedAttack(true);
	}
}

void ACarnivalMotorcycle::MountedPunch(bool bPunchRight)
{
	if (CurrentRider)
	{
		CurrentRider->PerformMountedAttack(false, bPunchRight);
	}
}

void ACarnivalMotorcycle::InputThrottle(float Value)
{
	ThrottleInput = Value;
}

void ACarnivalMotorcycle::InputSteering(float Value)
{
	SteeringInput = Value;
}

void ACarnivalMotorcycle::InputBrake(float Value)
{
	BrakeInput = Value;
}

void ACarnivalMotorcycle::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
}
