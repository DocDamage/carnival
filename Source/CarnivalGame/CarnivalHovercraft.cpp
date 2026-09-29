// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalHovercraft.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "NiagaraComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalVehicleExit.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "TimerManager.h"

ACarnivalHovercraft::ACarnivalHovercraft()
{
	PrimaryActorTick.bCanEverTick = true;

	CollisionBox = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionBox"));
	CollisionBox->SetBoxExtent(FVector(220.0f, 180.0f, 80.0f));
	CollisionBox->SetCollisionProfileName(TEXT("Vehicle"));
	CollisionBox->SetSimulatePhysics(false);
	RootComponent = CollisionBox;

	CraftMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CraftMesh"));
	CraftMesh->SetupAttachment(RootComponent);
	CraftMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	MountTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("MountTrigger"));
	MountTrigger->SetupAttachment(RootComponent);
	MountTrigger->SetBoxExtent(FVector(280.0f, 220.0f, 100.0f));
	MountTrigger->SetCollisionProfileName(TEXT("Trigger"));

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 800.0f;
	CameraBoom->SetRelativeRotation(FRotator(-12.0f, 0.0f, 0.0f));
	CameraBoom->SocketOffset = FVector(0.0f, 0.0f, 180.0f);
	CameraBoom->bUsePawnControlRotation = false;
	CameraBoom->bInheritPitch = false;
	CameraBoom->bInheritRoll = false;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 8.0f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	ThrusterVFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("ThrusterVFX"));
	ThrusterVFX->SetupAttachment(CraftMesh);
}

void ACarnivalHovercraft::BeginPlay()
{
	Super::BeginPlay();
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bInheritPitch = true;
	CameraBoom->bInheritYaw = true;
	CurrentHoverHeight = TargetHoverHeight;
}

void ACarnivalHovercraft::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	UpdateHoverPhysics(DeltaTime);
}

void ACarnivalHovercraft::UpdateHoverPhysics(float DeltaTime)
{
	// 1. 4-Corner Raycast Hover Suspension
	FVector Forward = GetActorForwardVector();
	FVector Right = GetActorRightVector();
	FVector Up = GetActorUpVector();

	FVector CheckPoints[4] = {
		GetActorLocation() + (Forward * 160.0f) + (Right * 110.0f),
		GetActorLocation() + (Forward * 160.0f) - (Right * 110.0f),
		GetActorLocation() - (Forward * 160.0f) + (Right * 110.0f),
		GetActorLocation() - (Forward * 160.0f) - (Right * 110.0f)
	};

	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);
	if (CurrentRider)
	{
		Params.AddIgnoredActor(CurrentRider);
	}

	float TotalHitZ = 0.0f;
	FVector AvgNormal = FVector::ZeroVector;
	int32 HitCount = 0;

	for (int32 i = 0; i < 4; ++i)
	{
		FHitResult Hit;
		FVector Start = CheckPoints[i] + (Up * 80.0f);
		FVector End = CheckPoints[i] - (Up * 350.0f);

		if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_WorldStatic, Params))
		{
			TotalHitZ += Hit.ImpactPoint.Z;
			AvgNormal += Hit.ImpactNormal;
			HitCount++;
		}
	}

	float TargetZ = GetActorLocation().Z;
	if (HitCount > 0)
	{
		float AvgGroundZ = TotalHitZ / (float)HitCount;
		AvgNormal.Normalize();
		TargetZ = AvgGroundZ + TargetHoverHeight;
		FallVelocity = 0.f;
	}
	else
	{
		AvgNormal = FVector::UpVector;
		FallVelocity += GetWorld()->GetGravityZ() * DeltaTime;
		TargetZ += FallVelocity * DeltaTime;
	}

	// 2. Speed & Propulsion
	float SpeedLimit = bIsBoosting ? MaxBoostSpeed : MaxForwardSpeed;
	float TargetForwardSpeed = SpeedLimit * ThrottleInput;
	float AccelRate = (FMath::Abs(TargetForwardSpeed) > FMath::Abs(CurrentForwardSpeed)) ? Acceleration : BrakingDeceleration;
	CurrentForwardSpeed = FMath::FInterpTo(CurrentForwardSpeed, TargetForwardSpeed, DeltaTime, AccelRate / 400.0f);

	float TargetStrafe = MaxStrafeSpeed * StrafeInput;
	CurrentStrafeSpeed = FMath::FInterpTo(CurrentStrafeSpeed, TargetStrafe, DeltaTime, Acceleration / 400.0f);

	// 3. Yaw Steering & Tilting
	float YawDelta = SteeringInput * TurnRate * DeltaTime;

	// Dynamic banking and pitch tilt
	float TargetBank = -(StrafeInput * 0.7f + SteeringInput * 0.3f) * MaxBankAngle;
	CurrentBank = FMath::FInterpTo(CurrentBank, TargetBank, DeltaTime, 5.0f);

	float TargetPitch = -ThrottleInput * MaxPitchAngle * 0.6f;
	CurrentPitch = FMath::FInterpTo(CurrentPitch, TargetPitch, DeltaTime, 4.0f);

	// 4. Ground Normal Alignment
	FRotator SurfaceRot = FRotationMatrix::MakeFromZX(AvgNormal, Forward).Rotator();
	FRotator NewRotation = FRotator(
		SurfaceRot.Pitch + CurrentPitch,
		GetActorRotation().Yaw + YawDelta,
		SurfaceRot.Roll + CurrentBank
	);

	// 5. Translation & Position Integration
	FVector MoveDelta = (Forward * CurrentForwardSpeed * DeltaTime) + (Right * CurrentStrafeSpeed * DeltaTime);
	FVector NewLocation = GetActorLocation() + MoveDelta;
	NewLocation.Z = HitCount > 0 ? FMath::FInterpTo(GetActorLocation().Z, TargetZ, DeltaTime, 7.0f) : TargetZ;

	FHitResult SweepHit;
	SetActorLocationAndRotation(NewLocation, NewRotation, true, &SweepHit);
	if (SweepHit.bBlockingHit)
	{
		CurrentForwardSpeed = CurrentStrafeSpeed = 0.f;
		FallVelocity = 0.f;
	}
}

void ACarnivalHovercraft::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	if (Cast<ACarnivalPlayerController>(GetController())) return;

	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ACarnivalHovercraft::InputThrottle);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACarnivalHovercraft::InputSteering);
	PlayerInputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &ACarnivalHovercraft::Dismount);
}

void ACarnivalHovercraft::InputThrottle(float Value)
{
	ThrottleInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalHovercraft::InputSteering(float Value)
{
	SteeringInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalHovercraft::InputStrafe(float Value)
{
	StrafeInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalHovercraft::InputBoost(bool bEnable)
{
	bIsBoosting = bEnable;
}

bool ACarnivalHovercraft::CanMount(AActor* PotentialRider) const
{
	const ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(PotentialRider);
	if (CurrentRider != nullptr || !IsValid(Player) || !Player->GetController()
		|| Player->MountedMotorcycle || Player->MountedBoat || Player->MountedHovercraft
		|| Player->IsUsingRide() || FMath::Abs(CurrentForwardSpeed) > 50.f || FMath::Abs(CurrentStrafeSpeed) > 50.f)
	{
		return false;
	}

	return MountTrigger->IsOverlappingActor(PotentialRider)
		&& CarnivalVehicleExit::CanReachSeat(this, Player, DriverRelativeOffset);
}

void ACarnivalHovercraft::Mount(ACarnivalPlayerCharacter* Rider)
{
	if (!CanMount(Rider))
	{
		return;
	}

	BoardingTransform = Rider->GetActorTransform();
	BoardingController = Rider->GetController();
	ClearControlInputs();
	CurrentRider = Rider;

	// Notify character
	Rider->OnMountHovercraft(this);

	// Possess hovercraft
	AController* RiderController = Rider->GetController();
	if (RiderController)
	{
		RiderController->Possess(this);
	}
}

void ACarnivalHovercraft::Dismount()
{
	if (FMath::Abs(CurrentForwardSpeed) <= 50.f && FMath::Abs(CurrentStrafeSpeed) <= 50.f) RestoreRider(false);
}

void ACarnivalHovercraft::ClearControlInputs()
{
	ThrottleInput = SteeringInput = StrafeInput = 0.f;
	bIsBoosting = false;
}

void ACarnivalHovercraft::UnPossessed()
{
	ClearControlInputs();
	Super::UnPossessed();
	if (CurrentRider && GetWorld()) GetWorld()->GetTimerManager().SetTimerForNextTick(
		FTimerDelegate::CreateUObject(this, &ACarnivalHovercraft::RecoverLostPossession));
}

void ACarnivalHovercraft::RecoverLostPossession()
{
	if (!GetController() && CurrentRider) RestoreRider(true);
}

void ACarnivalHovercraft::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (EndPlayReason == EEndPlayReason::Destroyed) RestoreRider(true);
	Super::EndPlay(EndPlayReason);
}

void ACarnivalHovercraft::RestoreRider(bool bEmergency)
{
	if (!IsValid(CurrentRider)) { CurrentRider = nullptr; return; }
	FVector Exit;
	if (!CarnivalVehicleExit::FindGroundExit(this, CurrentRider, CollisionBox->GetScaledBoxExtent(), Exit))
	{
		if (!bEmergency) return;
		Exit = BoardingTransform.GetLocation();
		FRotator Rotation = BoardingTransform.Rotator();
		GetWorld()->FindTeleportSpot(CurrentRider, Exit, Rotation);
	}
	ACarnivalPlayerCharacter* Rider = CurrentRider;
	AController* FormerController = BoardingController.Get();
	CurrentRider = nullptr;
	ClearControlInputs();
	CurrentForwardSpeed = CurrentStrafeSpeed = 0.f;
	Rider->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	Rider->SetActorLocationAndRotation(Exit, FRotator(0, GetActorRotation().Yaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
	Rider->OnDismountHovercraft();
	Rider->GetCharacterMovement()->StopMovementImmediately();
	if (FormerController && (!FormerController->GetPawn() || FormerController->GetPawn() == this)) FormerController->Possess(Rider);
	BoardingController.Reset();
}
