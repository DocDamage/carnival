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

	const FVector Before = GetActorLocation();
	UpdateHoverPhysics(DeltaTime);
	const float Seconds = FMath::Max(0.f, DeltaTime);
	const bool bBlocked = CurrentRider && BrakeInput <= .05f && (FMath::Abs(ThrottleInput) >= .1f || FMath::Abs(StrafeInput) >= .1f)
		&& DeltaTime > 0 && FVector::Dist2D(Before, GetActorLocation()) / DeltaTime < 20.f;
	BlockedControlDuration = bBlocked ? BlockedControlDuration + Seconds : 0.f;
	UnsupportedDuration = CurrentRider && !bHasHoverSupport ? UnsupportedDuration + Seconds : 0.f;
	if (bHasHoverSupport) LastSupportedZ = GetActorLocation().Z;
	if (CurrentRider && (UnsupportedDuration >= 8.f
		|| (UnsupportedDuration >= .5f && LastSupportedZ - GetActorLocation().Z >= 4000.f)))
		TryRecoverToBoardingPoint();
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

	bHasHoverSupport = HitCount > 0;
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
	float TargetForwardSpeed = BrakeInput > 0.f ? 0.f : SpeedLimit * ThrottleInput;
	float AccelRate = (FMath::Abs(TargetForwardSpeed) > FMath::Abs(CurrentForwardSpeed)) ? Acceleration : BrakingDeceleration;
	CurrentForwardSpeed = FMath::FInterpTo(CurrentForwardSpeed, TargetForwardSpeed, DeltaTime, AccelRate / 400.0f);

	float TargetStrafe = BrakeInput > 0.f ? 0.f : MaxStrafeSpeed * StrafeInput;
	CurrentStrafeSpeed = FMath::FInterpTo(CurrentStrafeSpeed, TargetStrafe, DeltaTime, Acceleration / 400.0f);
	if (BrakeInput > 0.f)
	{
		const float Rate = BrakingDeceleration * BrakeInput / 200.f;
		CurrentForwardSpeed = FMath::FInterpTo(CurrentForwardSpeed, 0.f, DeltaTime, Rate);
		CurrentStrafeSpeed = FMath::FInterpTo(CurrentStrafeSpeed, 0.f, DeltaTime, Rate);
	}

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

	// Averaging suspension rays can pitch the hull into a convex ramp join,
	// or leave the bow below a small step before the forward rays reach it.
	// Probe the full oriented hull for a nearby supporting surface. Vehicle
	// responses ignore water overlaps; the ordinary suspension still sets the
	// water height, and the final swept move still blocks walls and ceilings.
	const FCollisionShape HullShape = FCollisionShape::MakeBox(CollisionBox->GetScaledBoxExtent());
	// A small lookahead gets a stable top-face contact before the bow catches
	// a step's vertical edge. The final physical sweep still decides movement.
	const FVector Lookahead = FVector(MoveDelta.X, MoveDelta.Y, 0).GetSafeNormal() * 20.f;
	for (const FVector Probe : {NewLocation, NewLocation + Lookahead})
	{
		FHitResult HullSupport;
		if (GetWorld()->SweepSingleByProfile(HullSupport, Probe + FVector(0, 0, 50.f), Probe,
			NewRotation.Quaternion(), CollisionBox->GetCollisionProfileName(), HullShape, Params)
			&& !HullSupport.bStartPenetrating && HullSupport.Normal.Z >= .7f)
		{
			NewLocation.Z = FMath::Max(NewLocation.Z, HullSupport.Location.Z + 2.f);
		}
	}

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

void ACarnivalHovercraft::InputBrake(float Value)
{
	BrakeInput = FMath::Clamp(Value, 0.f, 1.f);
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
	BoardingVehicleTransform = GetActorTransform();
	bHasBoardingVehicleTransform = true;
	BlockedControlDuration = UnsupportedDuration = 0.f;
	LastSupportedZ = GetActorLocation().Z;
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
	if (CanRecoverToBoardingPoint() && TryRecoverToBoardingPoint()) return;
	if (FMath::Abs(CurrentForwardSpeed) <= 50.f && FMath::Abs(CurrentStrafeSpeed) <= 50.f) RestoreRider(false);
}

bool ACarnivalHovercraft::CanRecoverToBoardingPoint() const
{
	return IsValid(CurrentRider) && GetController() && GetController() == BoardingController.Get()
		&& bHasBoardingVehicleTransform && (BlockedControlDuration >= 2.f || UnsupportedDuration >= 2.f
			|| (UnsupportedDuration >= .5f && LastSupportedZ - GetActorLocation().Z >= 4000.f));
}

bool ACarnivalHovercraft::TryRecoverToBoardingPoint()
{
	if (!CanRecoverToBoardingPoint()
		|| !CarnivalVehicleExit::IsRecoveryPoseClear(this, CurrentRider, CollisionBox, BoardingVehicleTransform)) return false;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(HoverRecoverySupport), false, this);
	Params.AddIgnoredActor(CurrentRider);
	int32 Supports = 0;
	for (float X : {-160.f, 160.f}) for (float Y : {-110.f, 110.f})
	{
		const FVector Point = BoardingVehicleTransform.TransformPositionNoScale(FVector(X, Y, 0));
		FHitResult Hit;
		if (GetWorld()->LineTraceSingleByChannel(Hit, Point + FVector(0, 0, 80), Point - FVector(0, 0, 350),
			ECC_WorldStatic, Params) && Hit.ImpactNormal.Z >= .7f) ++Supports;
	}
	if (Supports < 2) return false;
	if (!SetActorLocationAndRotation(BoardingVehicleTransform.GetLocation(), BoardingVehicleTransform.Rotator(),
		false, nullptr, ETeleportType::TeleportPhysics)) return false;
	ClearControlInputs();
	CurrentForwardSpeed = CurrentStrafeSpeed = CurrentBank = CurrentPitch = FallVelocity = 0.f;
	BlockedControlDuration = UnsupportedDuration = 0.f;
	LastSupportedZ = GetActorLocation().Z;
	CarnivalVehicleExit::NotifyRecovery(CurrentRider);
	return true;
}

void ACarnivalHovercraft::ClearControlInputs()
{
	ThrottleInput = SteeringInput = StrafeInput = BrakeInput = 0.f;
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
