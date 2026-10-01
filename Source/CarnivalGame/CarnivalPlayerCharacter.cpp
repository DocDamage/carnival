// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalPlayerCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalWeaponBase.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalActivityBase.h"
#include "CarnivalLadder.h"
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalDoorSubsystem.h"
#include "CarnivalWaterVolume.h"
#include "CarnivalCharacterMovementComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Components/CapsuleComponent.h"

ACarnivalPlayerCharacter::ACarnivalPlayerCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer.SetDefaultSubobjectClass<UCarnivalCharacterMovementComponent>(ACharacter::CharacterMovementComponentName))
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.0f);
	DefaultCapsuleHalfHeight = 96.0f;
	DefaultCapsuleRadius = 42.0f;

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	GetCharacterMovement()->JumpZVelocity = 550.f;
	GetCharacterMovement()->AirControl = 0.35f;
	GetCharacterMovement()->MaxWalkSpeed = 450.f;
	GetCharacterMovement()->MinAnalogWalkSpeed = 20.f;
	GetCharacterMovement()->BrakingDecelerationWalking = 2000.f;
	GetCharacterMovement()->BrakingDecelerationFalling = 1500.0f;
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
	GetCharacterMovement()->NavAgentProps.bCanSwim = true;

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 350.0f;
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->SetRelativeLocation(FVector(0.0f, 0.0f, 60.0f));

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	BuildComponent = CreateDefaultSubobject<UCarnivalBuildComponent>(TEXT("BuildComponent"));
    RidePassenger = CreateDefaultSubobject<UCarnivalRidePassengerComponent>(TEXT("RidePassenger"));

	WalkSpeed = 200.0f;
	JogSpeed = 450.0f;
	SprintSpeed = 750.0f;
	CrouchSpeed = 220.0f;
	ProneSpeed = 120.0f;
	SwimSpeed = 300.0f;
	GetCharacterMovement()->MaxSwimSpeed = SwimSpeed;
	SwimIdleAnimation = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Carnival/Character/Animations/Swim/anim_SwimIdle.anim_SwimIdle")));
	SwimForwardAnimation = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Carnival/Character/Animations/Swim/anim_Swim_Surface_Fwd.anim_Swim_Surface_Fwd")));
	SwimLeftAnimation = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Carnival/Character/Animations/Swim/anim_Swim_Surface_Left.anim_Swim_Surface_Left")));
	SwimRightAnimation = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Carnival/Character/Animations/Swim/anim_Swim_Surface_Right.anim_Swim_Surface_Right")));
	UnderwaterPostProcessMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/Carnival/World/Materials/Water/M_CarnivalUnderwaterPP.M_CarnivalUnderwaterPP")));
	GetCharacterMovement()->Buoyancy = 1.0f;
	// Off until the camera is inside water; the settings below are the underwater grade.
	FollowCamera->PostProcessBlendWeight = 0.0f;
	FollowCamera->PostProcessSettings.bOverride_ColorSaturation = true;
	FollowCamera->PostProcessSettings.ColorSaturation = FVector4(0.75f, 0.85f, 0.95f, 1.0f);
	FollowCamera->PostProcessSettings.bOverride_ColorGain = true;
	FollowCamera->PostProcessSettings.ColorGain = FVector4(0.7f, 0.95f, 1.05f, 1.0f);
	FollowCamera->PostProcessSettings.bOverride_VignetteIntensity = true;
	FollowCamera->PostProcessSettings.VignetteIntensity = 0.65f;
	RollLandingVelocityThreshold = -900.0f;

	LocomotionState = ECarnivalLocomotionState::Jogging;
	bIsProne = false;
	MountedMotorcycle = nullptr;
	CurrentWeapon = nullptr;
}

void ACarnivalPlayerCharacter::BeginPlay()
{
	Super::BeginPlay();
    RidePassenger->OnBoarded.AddDynamic(this, &ACarnivalPlayerCharacter::HandleRideBoarded);
    RidePassenger->OnUnboarded.AddDynamic(this, &ACarnivalPlayerCharacter::HandleRideUnboarded);

	// Default to equipping sword if available
	if (DefaultSwordClass)
	{
		EquipWeaponSlot(1);
	}
}

void ACarnivalPlayerCharacter::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (IsParkourTraversing())
	{
		UpdateParkourTraversal(DeltaTime);
		return;
	}
    if (OperatingRide && (!IsValid(OperatingRide) || OperatingRide->PlayerOperator != this))
    {
        OperatingRide = nullptr;
        GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    }
    if (IsUsingRide())
    {
        BlockedInputDuration = SwimmingDuration = FallingDuration = 0.f;
        UpdateSwimAnimation();
        UpdateUnderwaterLook();
        return;
    }

	UpdateWaterMovement(DeltaTime);
	UpdateSafeRecoveryState(DeltaTime);
	UpdateSwimAnimation();
	UpdateUnderwaterLook();

	// Update movement state based on movement component
	if (LocomotionState != ECarnivalLocomotionState::RidingMotorcycle &&
		LocomotionState != ECarnivalLocomotionState::DrivingBoat &&
		LocomotionState != ECarnivalLocomotionState::PilotingHovercraft &&
		LocomotionState != ECarnivalLocomotionState::Vaulting &&
		LocomotionState != ECarnivalLocomotionState::Mantling &&
		LocomotionState != ECarnivalLocomotionState::LandingRoll)
	{
		if (GetCharacterMovement()->IsSwimming())
		{
			LocomotionState = ECarnivalLocomotionState::Swimming;
		}
		else if (GetCharacterMovement()->IsFalling())
		{
			LocomotionState = ECarnivalLocomotionState::Falling;
		}
		else if (bIsProne)
		{
			LocomotionState = ECarnivalLocomotionState::Prone;
		}
		else if (bIsCrouched)
		{
			LocomotionState = ECarnivalLocomotionState::Crouching;
		}
		else
		{
			float Speed = GetVelocity().Size2D();
			if (Speed > JogSpeed + 50.0f)
			{
				LocomotionState = ECarnivalLocomotionState::Sprinting;
			}
			else if (Speed > WalkSpeed + 20.0f)
			{
				LocomotionState = ECarnivalLocomotionState::Jogging;
			}
			else if (Speed > 10.0f)
			{
				LocomotionState = ECarnivalLocomotionState::Walking;
			}
			else
			{
				LocomotionState = ECarnivalLocomotionState::Jogging;
			}
		}
	}
	else if (LocomotionState == ECarnivalLocomotionState::RidingMotorcycle)
	{
		UAnimMontage* ActiveMontage = GetCurrentMontage();
		UAnimInstance* RiderAnim = GetMesh()->GetAnimInstance();
		const bool bMountAtSeat = RiderAnim && ActiveMontage
			&& (ActiveMontage == MountLeftMontage || ActiveMontage == MountRightMontage)
			&& RiderAnim->Montage_GetPosition(ActiveMontage) >= ActiveMontage->GetPlayLength() - .02f;
		// Fitted mounts hold the seated end. Blend directly into riding idle
		// instead of blending out through the standing locomotion graph.
		if (RidingIdleMontage && (!ActiveMontage || bMountAtSeat))
		{
			PlayAnimMontage(RidingIdleMontage, 1.0f);
			if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
			{
				const FName Section = RidingIdleMontage->GetSectionName(0);
				if (!Section.IsNone()) Anim->Montage_SetNextSection(Section, Section, RidingIdleMontage);
			}
		}
	}
}

void ACarnivalPlayerCharacter::UpdateSafeRecoveryState(float DeltaTime)
{
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	if (!Movement || !GetWorld()) return;

	const bool bSwimming = Movement->IsSwimming() || Movement->IsInWater();
	const bool bFalling = Movement->IsFalling();
	// Authored swimming water (river, flooded Atlantis) is meant to be swum in, so it does not count as being
	// stranded; the pause menu's Return to path still gets the player out. Other water still offers recovery.
	const bool bAuthoredWater = Cast<ACarnivalWaterVolume>(Movement->GetPhysicsVolume()) != nullptr;
	SwimmingDuration = bSwimming && !bAuthoredWater ? SwimmingDuration + DeltaTime : 0.f;
	FallingDuration = bFalling ? FallingDuration + DeltaTime : 0.f;

	const FVector Acceleration = Movement->GetCurrentAcceleration();
	const float InputThreshold = FMath::Max(60.f, Movement->GetMaxAcceleration() * .2f);
	const bool bHasMovementIntent = Acceleration.Size2D() >= InputThreshold
		|| GetLastMovementInputVector().Size2D() >= .25f
		|| GetPendingMovementInputVector().Size2D() >= .25f;
	const bool bBlockedWhileTryingToMove = Movement->IsMovingOnGround()
		&& !bSwimming
		&& bHasMovementIntent
		&& GetVelocity().Size2D() < 24.f;
	BlockedInputDuration = bBlockedWhileTryingToMove ? BlockedInputDuration + DeltaTime : 0.f;

	// Keep a recent full-height, walkable position. Crouched and prone locations
	// are excluded so recovery can safely restore the player's normal capsule.
	const bool bSafeGround = Movement->IsMovingOnGround() && !bSwimming && !bFalling
		&& !bIsCrouched && !bIsProne
		&& GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics;
	if (bSafeGround)
	{
		SafeLocationRefreshTime -= DeltaTime;
		if (!bHasSafeRecoveryLocation || SafeLocationRefreshTime <= 0.f)
		{
			LastSafeRecoveryLocation = GetActorLocation();
			LastSafeRecoveryRotation = FRotator(0.f, GetActorRotation().Yaw, 0.f);
			bHasSafeRecoveryLocation = true;
			SafeLocationRefreshTime = .25f;
		}
	}
	else
	{
		SafeLocationRefreshTime = 0.f;
	}
}

bool ACarnivalPlayerCharacter::CanRecoverToSafePosition() const
{
	if (!bHasSafeRecoveryLocation || !GetWorld() || IsUsingRide()
		|| MountedMotorcycle || MountedBoat || MountedHovercraft)
	{
		return false;
	}

	const AWorldSettings* WorldSettings = GetWorld()->GetWorldSettings();
	const bool bBelowKillPlane = WorldSettings && GetActorLocation().Z < WorldSettings->KillZ + 500.f;
	return BlockedInputDuration >= BlockedInputRecoveryDelay
		|| SwimmingDuration >= SwimmingRecoveryDelay
		|| FallingDuration >= FallingRecoveryDelay
		|| bBelowKillPlane;
}

void ACarnivalPlayerCharacter::ResetRecoveryAfterLoad()
{
	LastSafeRecoveryLocation = GetActorLocation();
	LastSafeRecoveryRotation = FRotator(0.f, GetActorRotation().Yaw, 0.f);
	bHasSafeRecoveryLocation = true;
	BlockedInputDuration = SwimmingDuration = FallingDuration = 0.f;
	SafeLocationRefreshTime = 0.f;
}

bool ACarnivalPlayerCharacter::FindSafeRecoveryLocation(FVector& OutLocation) const
{
	return FindClearStandingLocation(LastSafeRecoveryLocation, OutLocation);
}

bool ACarnivalPlayerCharacter::FindClearStandingLocation(const FVector& Around, FVector& OutLocation) const
{
	if (!GetWorld() || !GetCapsuleComponent() || !GetCharacterMovement()) return false;

	const float Radius = DefaultCapsuleRadius * GetCapsuleComponent()->GetShapeScale();
	const float HalfHeight = DefaultCapsuleHalfHeight * GetCapsuleComponent()->GetShapeScale();
	const FCollisionShape StandingCapsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	const FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(PlayerSafeRecovery), false, this);
	const FVector Offsets[] = {
		FVector::ZeroVector,
		FVector(70.f, 0.f, 0.f), FVector(-70.f, 0.f, 0.f), FVector(0.f, 70.f, 0.f), FVector(0.f, -70.f, 0.f),
		FVector(140.f, 0.f, 0.f), FVector(-140.f, 0.f, 0.f), FVector(0.f, 140.f, 0.f), FVector(0.f, -140.f, 0.f),
		FVector(70.f, 70.f, 0.f), FVector(70.f, -70.f, 0.f), FVector(-70.f, 70.f, 0.f), FVector(-70.f, -70.f, 0.f)
	};

	for (const FVector& Offset : Offsets)
	{
		const FVector Sample = Around + Offset;
		const FVector TraceStart = Sample + FVector(0.f, 0.f, 80.f);
		const FVector TraceEnd = Sample - FVector(0.f, 0.f, HalfHeight + 130.f);
		FHitResult FloorHit;
		if (!GetWorld()->LineTraceSingleByChannel(FloorHit, TraceStart, TraceEnd, ECC_Visibility, QueryParams)
			|| !FloorHit.bBlockingHit
			|| FloorHit.ImpactNormal.Z < GetCharacterMovement()->GetWalkableFloorZ())
		{
			continue;
		}

		const FVector Candidate(FloorHit.ImpactPoint.X, FloorHit.ImpactPoint.Y, FloorHit.ImpactPoint.Z + HalfHeight + 2.f);
		if (GetWorld()->OverlapBlockingTestByChannel(Candidate, FQuat::Identity, ECC_Pawn, StandingCapsule, QueryParams))
		{
			continue;
		}

		OutLocation = Candidate;
		return true;
	}
	return false;
}

bool ACarnivalPlayerCharacter::TryRecoverToSafePosition()
{
	if (!CanRecoverToSafePosition()) return false;

	FVector RecoveryLocation;
	if (!FindSafeRecoveryLocation(RecoveryLocation)) return false;
	return StandAndTeleport(RecoveryLocation, LastSafeRecoveryRotation);
}

const FName ACarnivalPlayerCharacter::RouteAnchorTag(TEXT("CarnivalRouteAnchor"));

bool ACarnivalPlayerCharacter::ReturnToNearestRoute()
{
	if (!GetWorld() || IsUsingRide() || MountedMotorcycle || MountedBoat || MountedHovercraft
		|| IsParkourTraversing() || ActiveActivity)
	{
		return false;
	}

	TArray<AActor*> Anchors;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (It->ActorHasTag(RouteAnchorTag)) Anchors.Add(*It);
	}
	const FVector Here = GetActorLocation();
	Anchors.Sort([&Here](const AActor& A, const AActor& B)
	{
		return FVector::DistSquared(A.GetActorLocation(), Here) < FVector::DistSquared(B.GetActorLocation(), Here);
	});

	// The nearest anchor can be momentarily occupied (a vehicle, a guest); try a few.
	for (int32 Index = 0; Index < FMath::Min(Anchors.Num(), 8); ++Index)
	{
		FVector Location;
		if (FindClearStandingLocation(Anchors[Index]->GetActorLocation(), Location)
			&& StandAndTeleport(Location, FRotator(0.f, Anchors[Index]->GetActorRotation().Yaw, 0.f)))
		{
			return true;
		}
	}
	return false;
}

bool ACarnivalPlayerCharacter::StandAndTeleport(const FVector& Location, const FRotator& Rotation)
{
	if (bIsCrouched) UnCrouch();
	bIsProne = false;
	GetCapsuleComponent()->SetCapsuleSize(DefaultCapsuleRadius, DefaultCapsuleHalfHeight, true);
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -DefaultCapsuleHalfHeight));
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	ConsumeMovementInputVector();

	if (!SetActorLocationAndRotation(Location, Rotation, false, nullptr, ETeleportType::TeleportPhysics)) return false;

	SetLocomotionState(ECarnivalLocomotionState::Jogging);
	GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
	BlockedInputDuration = SwimmingDuration = FallingDuration = 0.f;
	LastSafeRecoveryLocation = Location;
	LastSafeRecoveryRotation = FRotator(0.f, Rotation.Yaw, 0.f);
	bHasSafeRecoveryLocation = true;
	return true;
}

void ACarnivalPlayerCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	float FallVelocityZ = GetVelocity().Z;
	if (FallVelocityZ < RollLandingVelocityThreshold && LandingRollMontage)
	{
		SetLocomotionState(ECarnivalLocomotionState::LandingRoll);
		PlayAnimMontage(LandingRollMontage);
	}
}

void ACarnivalPlayerCharacter::SetLocomotionState(ECarnivalLocomotionState NewState)
{
	LocomotionState = NewState;
}

void ACarnivalPlayerCharacter::StartSprinting()
{
	if (IsParkourTraversing()) return;
    if (IsUsingRide()) return;
	if (!bIsCrouched && !bIsProne && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		GetCharacterMovement()->MaxWalkSpeed = SprintSpeed;
		LocomotionState = ECarnivalLocomotionState::Sprinting;
	}
}

void ACarnivalPlayerCharacter::StopSprinting()
{
	if (IsParkourTraversing()) return;
	if (!bIsCrouched && !bIsProne && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
		LocomotionState = ECarnivalLocomotionState::Jogging;
	}
}

void ACarnivalPlayerCharacter::ToggleCrouch()
{
	if (IsParkourTraversing()) return;
    if (IsUsingRide()) return;
	if (bIsProne)
	{
		ToggleProne(); // Exit prone first
		return;
	}

	if (bIsCrouched)
	{
		UnCrouch();
		GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
	}
	else
	{
		Crouch();
		GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
	}
}

void ACarnivalPlayerCharacter::ToggleProne()
{
	if (IsParkourTraversing()) return;
    if (IsUsingRide()) return;
	if (bIsProne)
	{
		const float Scale = GetCapsuleComponent()->GetShapeScale();
		const FVector StandingLocation = GetActorLocation() + FVector(0, 0,
			(DefaultCapsuleHalfHeight - GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()) * Scale);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalProneClearance), false, this);
		if (GetWorld()->OverlapBlockingTestByProfile(StandingLocation, FQuat::Identity, TEXT("Pawn"),
			FCollisionShape::MakeCapsule(DefaultCapsuleRadius * Scale, DefaultCapsuleHalfHeight * Scale), Params)) return;
		// Preserve the feet position and only stand after checking the full capsule.
		SetActorLocation(StandingLocation);
		bIsProne = false;
		GetCapsuleComponent()->SetCapsuleSize(DefaultCapsuleRadius, DefaultCapsuleHalfHeight);
		GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -DefaultCapsuleHalfHeight));
		GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
		if (ProneToStandMontage)
		{
			PlayAnimMontage(ProneToStandMontage);
		}
	}
	else
	{
		// Enter prone
		if (bIsCrouched)
		{
			UnCrouch();
			if (bIsCrouched) return;
		}
		const float Lowering = (GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() - 30.f)
			* GetCapsuleComponent()->GetShapeScale();
		bIsProne = true;
		LocomotionState = ECarnivalLocomotionState::Prone;
		GetCapsuleComponent()->SetCapsuleSize(FMath::Min(DefaultCapsuleRadius, 30.f), 30.0f);
		SetActorLocation(GetActorLocation() - FVector(0, 0, Lowering), true);
		GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -30.0f));
		GetCharacterMovement()->MaxWalkSpeed = ProneSpeed;
		if (StandToProneMontage)
		{
			PlayAnimMontage(StandToProneMontage);
		}
	}
}

bool ACarnivalPlayerCharacter::TryVaultOrMantle()
{
	if (IsParkourTraversing()) return true;
	if (IsUsingRide() || MountedMotorcycle || MountedBoat || MountedHovercraft || bIsProne || bIsCrouched
		|| !GetCharacterMovement()->IsMovingOnGround()) return false;
	const FVector Start = GetActorLocation();
	const FVector Forward = FRotator(0, GetActorRotation().Yaw, 0).Vector();
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const float Radius = GetCapsuleComponent()->GetScaledCapsuleRadius();
	const float FeetZ = Start.Z - HalfHeight;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalParkour), false, this);
	FHitResult Wall, Top;
	const FVector LowStart(Start.X, Start.Y, FeetZ + 50.f);
	if (!GetWorld()->LineTraceSingleByChannel(Wall, LowStart, LowStart + Forward * 130.f, ECC_Visibility, Params)
		|| Wall.ImpactNormal.Z > .4f) return false;
	FVector TopProbe = Wall.ImpactPoint + Forward * 10.f;
	TopProbe.Z = FeetZ + 250.f;
	if (!GetWorld()->LineTraceSingleByChannel(Top, TopProbe, TopProbe - FVector(0, 0, 250), ECC_Visibility, Params)
		|| Top.ImpactNormal.Z < GetCharacterMovement()->GetWalkableFloorZ()) return false;
	const float Height = Top.ImpactPoint.Z - FeetZ;
	if (Height < 40.f || Height > 230.f) return false;
	FVector Destination = Wall.ImpactPoint + Forward * (Radius + 8.f);
	Destination.Z = Top.ImpactPoint.Z + HalfHeight + 3.f;
	bool bVault = false;
	if (Height <= 115.f)
	{
		FVector LandingProbe = Wall.ImpactPoint + Forward * 200.f;
		LandingProbe.Z = Top.ImpactPoint.Z + 10.f;
		FHitResult Landing;
		if (GetWorld()->LineTraceSingleByChannel(Landing, LandingProbe,
			LandingProbe - FVector(0, 0, Height + 60.f), ECC_Visibility, Params)
			&& Landing.ImpactNormal.Z >= GetCharacterMovement()->GetWalkableFloorZ()
			&& Landing.ImpactPoint.Z < Top.ImpactPoint.Z - 20.f)
		{
			Destination = Landing.ImpactPoint + FVector(0, 0, HalfHeight + 3.f);
			bVault = true;
		}
	}
	if (!bVault)
	{
		FHitResult Landing;
		if (!GetWorld()->LineTraceSingleByChannel(Landing, Destination,
			Destination - FVector(0, 0, HalfHeight + 10.f), ECC_Visibility, Params)
			|| Landing.ImpactNormal.Z < GetCharacterMovement()->GetWalkableFloorZ()
			|| FMath::Abs(Landing.ImpactPoint.Z - Top.ImpactPoint.Z) > 5.f) return false;
	}
	const float ClearanceZ = Top.ImpactPoint.Z + HalfHeight + 5.f;
	const TArray<FVector> Path = {FVector(Start.X, Start.Y, ClearanceZ),
		FVector(Destination.X, Destination.Y, ClearanceZ), Destination};
	return BeginParkourTraversal(Path, bVault ? ECarnivalLocomotionState::Vaulting : ECarnivalLocomotionState::Mantling,
		bVault ? VaultMontage : (Height <= 170.f ? Mantle1MMontage : Mantle2MMontage));
}

bool ACarnivalPlayerCharacter::TryLadderClimb()
{
	if (IsParkourTraversing()) return true;
	if (IsUsingRide() || MountedMotorcycle || MountedBoat || MountedHovercraft || bIsProne || bIsCrouched
		|| !GetCharacterMovement()->IsMovingOnGround()) return false;
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	for (TActorIterator<ACarnivalLadder> It(GetWorld()); It; ++It)
	{
		const FVector Bottom = It->BottomExit->GetComponentLocation() + FVector(0, 0, HalfHeight + 3.f);
		const FVector Top = It->TopExit->GetComponentLocation() + FVector(0, 0, HalfHeight + 3.f);
		if (Top.Z - Bottom.Z < 80.f) continue;
		const float BottomDistance = FVector::Dist(GetActorLocation(), Bottom);
		const float TopDistance = FVector::Dist(GetActorLocation(), Top);
		const bool bGoingUp = BottomDistance <= TopDistance;
		if (FMath::Min(BottomDistance, TopDistance) > It->InteractionDistance) continue;
		const FVector Destination = bGoingUp ? Top : Bottom;
		FHitResult Floor;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalLadder), false, this);
		if (!GetWorld()->LineTraceSingleByChannel(Floor, Destination,
			Destination - FVector(0, 0, HalfHeight + 20.f), ECC_Visibility, Params)
			|| Floor.ImpactNormal.Z < GetCharacterMovement()->GetWalkableFloorZ()
			|| FMath::Abs(Floor.ImpactPoint.Z + HalfHeight + 3.f - Destination.Z) > 8.f) continue;
		const FVector AboveBottom(Bottom.X, Bottom.Y, Top.Z);
		const TArray<FVector> Path = bGoingUp ? TArray<FVector>{Bottom, AboveBottom, Top}
			: TArray<FVector>{Top, AboveBottom, Bottom};
		if (BeginParkourTraversal(Path, ECarnivalLocomotionState::LadderClimbing, nullptr)) return true;
	}
	return false;
}

bool ACarnivalPlayerCharacter::BeginParkourTraversal(const TArray<FVector>& Path,
	ECarnivalLocomotionState State, UAnimMontage* Montage)
{
	if (Path.IsEmpty()) return false;
	const auto Shape = FCollisionShape::MakeCapsule(GetCapsuleComponent()->GetScaledCapsuleRadius(),
		GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalParkourClearance), false, this);
	FVector Previous = GetActorLocation();
	for (const FVector& Point : Path)
	{
		FHitResult Hit;
		if (GetWorld()->OverlapBlockingTestByProfile(Point, FQuat::Identity, TEXT("Pawn"), Shape, Params)
			|| GetWorld()->SweepSingleByProfile(Hit, Previous, Point, FQuat::Identity, TEXT("Pawn"), Shape, Params)) return false;
		Previous = Point;
	}
	ParkourPath = Path;
	ParkourPointIndex = 0;
	if (BuildComponent && BuildComponent->bIsBuildModeActive) BuildComponent->ToggleBuildMode();
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	ConsumeMovementInputVector();
	SetLocomotionState(State);
	if (Montage) PlayAnimMontage(Montage);
	return true;
}

void ACarnivalPlayerCharacter::UpdateParkourTraversal(float DeltaTime)
{
	float Remaining = FMath::Max(0.f, DeltaTime) * FMath::Max(50.f, ParkourTraversalSpeed);
	while (ParkourPath.IsValidIndex(ParkourPointIndex) && Remaining > 0.f)
	{
		const FVector Current = GetActorLocation();
		const FVector Delta = ParkourPath[ParkourPointIndex] - Current;
		const float Distance = Delta.Size();
		if (Distance < .1f) { ++ParkourPointIndex; continue; }
		const float Step = FMath::Min(Remaining, Distance);
		FHitResult Hit;
		SetActorLocation(Current + Delta * (Step / Distance), true, &Hit);
		if (Hit.bBlockingHit) { CancelParkourTraversal(); return; }
		Remaining -= Step;
		if (Step >= Distance - .1f) ++ParkourPointIndex;
	}
	if (!ParkourPath.IsValidIndex(ParkourPointIndex)) CancelParkourTraversal();
}

void ACarnivalPlayerCharacter::CancelParkourTraversal()
{
	if (!IsParkourTraversing()) return;
	ParkourPath.Reset();
	if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->Montage_Stop(0.f);
	GetMesh()->ConsumeRootMotion();
	GetCharacterMovement()->StopMovementImmediately();
	ConsumeMovementInputVector();
	FHitResult Floor;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalParkourLanding), false, this);
	const bool bSupported = GetWorld()->LineTraceSingleByChannel(Floor, GetActorLocation(),
		GetActorLocation() - FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 10.f), ECC_Visibility, Params)
		&& Floor.ImpactNormal.Z >= GetCharacterMovement()->GetWalkableFloorZ();
	GetCharacterMovement()->SetMovementMode(bSupported ? MOVE_Walking : MOVE_Falling);
	SetLocomotionState(bSupported ? ECarnivalLocomotionState::Jogging : ECarnivalLocomotionState::Falling);
}

void ACarnivalPlayerCharacter::TryInteractOrMount()
{
	if (IsParkourTraversing()) return;
    if (OperatingRide) return;
    if (RidePassenger->IsRiding())
    {
        if (auto* Operation = RidePassenger->GetCurrentRide()->FindComponentByClass<UCarnivalRideOperationComponent>())
            Operation->RequestPassengerExit(this);
        return;
    }
    if (auto* Attendant = FindNearbyAttendant())
    {
        Attendant->Operation->RequestBoard(this);
        return;
    }
	// Check for nearby motorcycle
	TArray<AActor*> OverlappingActors;
	TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
	ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_Pawn));
	ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_Vehicle));

	UKismetSystemLibrary::SphereOverlapActors(
		this,
		GetActorLocation(),
		220.0f,
		ObjectTypes,
		ACarnivalMotorcycle::StaticClass(),
		TArray<AActor*>(),
		OverlappingActors
	);

	ACarnivalMotorcycle* ClosestRecoverableBike = nullptr;
	float ClosestRecoverableDistanceSquared = TNumericLimits<float>::Max();
	for (AActor* Actor : OverlappingActors)
	{
		ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(Actor);
		if (Bike && Bike->CanRecoverFromStuckOrOverturned())
		{
			const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Bike->GetActorLocation());
			if (DistanceSquared < ClosestRecoverableDistanceSquared)
			{
				ClosestRecoverableBike = Bike;
				ClosestRecoverableDistanceSquared = DistanceSquared;
			}
		}
	}
	if (ClosestRecoverableBike)
	{
		// The first press rights the bike while leaving the player on foot. A
		// second press uses the ordinary mount path after the recovery completes.
		ClosestRecoverableBike->TryRecoverFromStuckOrOverturned();
		return;
	}
	for (AActor* Actor : OverlappingActors)
	{
		if (ACarnivalMotorcycle* Bike = Cast<ACarnivalMotorcycle>(Actor))
		{
			bool bMountLeft = true;
			if (Bike->CanMount(this, bMountLeft))
			{
				Bike->Mount(this, bMountLeft);
				return;
			}
		}
	}

	// 3. Check for nearby boat
	TArray<AActor*> OverlappingBoats;
	UKismetSystemLibrary::SphereOverlapActors(
		this,
		GetActorLocation(),
		350.0f,
		ObjectTypes,
		ACarnivalBoat::StaticClass(),
		TArray<AActor*>(),
		OverlappingBoats
	);

	for (AActor* Actor : OverlappingBoats)
	{
		ACarnivalBoat* Boat = Cast<ACarnivalBoat>(Actor);
		if (Boat && Boat->CanMount(this))
		{
			Boat->Mount(this);
			return;
		}
	}

	// 4. Check for nearby hovercraft
	TArray<AActor*> OverlappingHover;
	UKismetSystemLibrary::SphereOverlapActors(
		this,
		GetActorLocation(),
		300.0f,
		ObjectTypes,
		ACarnivalHovercraft::StaticClass(),
		TArray<AActor*>(),
		OverlappingHover
	);

	for (AActor* Actor : OverlappingHover)
	{
		ACarnivalHovercraft* Hover = Cast<ACarnivalHovercraft>(Actor);
		if (Hover && Hover->CanMount(this))
		{
			Hover->Mount(this);
			return;
		}
	}
}

void ACarnivalPlayerCharacter::TryContextInteract()
{
	if (IsParkourTraversing()) return;
	if (ACarnivalMissionInteractionActor* MissionInteraction = FindNearbyMissionInteraction())
	{
		MissionInteraction->TryInteract(this);
		return;
	}
	if (ActiveActivity && (ActiveActivity->ActivityState == ECarnivalActivityState::Completed
		|| ActiveActivity->ActivityState == ECarnivalActivityState::Failed))
	{
		ActiveActivity->ResetActivity();
		ActiveActivity = nullptr;
		return;
	}
	if (NearbyActivity && NearbyActivity->ActivityState != ECarnivalActivityState::Active)
	{
		NearbyActivity->StartActivity(this);
		return;
	}
	if (AActor* Door = FindNearbyDoor())
	{
		GetWorld()->GetSubsystem<UCarnivalDoorSubsystem>()->ToggleDoor(Door, GetActorLocation());
		return;
	}
	InteractWithRideOperator();
}

AActor* ACarnivalPlayerCharacter::FindNearbyDoor() const
{
	if (LocomotionState != ECarnivalLocomotionState::Walking && LocomotionState != ECarnivalLocomotionState::Jogging
		&& LocomotionState != ECarnivalLocomotionState::Sprinting && LocomotionState != ECarnivalLocomotionState::Crouching) return nullptr;
	const UCarnivalDoorSubsystem* Doors = GetWorld() ? GetWorld()->GetSubsystem<UCarnivalDoorSubsystem>() : nullptr;
	return Doors ? Doors->FindDoorNear(GetActorLocation()) : nullptr;
}

bool ACarnivalPlayerCharacter::IsInWaterVolume() const
{
	return GetCharacterMovement() && GetCharacterMovement()->IsInWater();
}

void ACarnivalPlayerCharacter::UpdateWaterMovement(float DeltaTime)
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const APhysicsVolume* Volume = Move->GetPhysicsVolume();
	const ACarnivalWaterVolume* Water = Cast<ACarnivalWaterVolume>(Volume);
	const bool bInWater = Volume && Volume->bWaterVolume;
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	bSubmerged = bInWater && (!Water || GetActorLocation().Z + HalfHeight < Water->GetSurfaceZ() - 5.f);
	const bool bWasSeabed = bSeabedWalking;
	bSeabedWalking = false;
	if (bClimbingOut)
	{
		if (!Move->IsFalling()) bClimbingOut = false;
		else if (GetActorLocation().Z - HalfHeight > ClimbOutLedgeZ + 5.f)
		{
			Move->Velocity.X = ClimbOutDirection.X * 250.f;
			Move->Velocity.Y = ClimbOutDirection.Y * 250.f;
			bClimbingOut = false;
		}
	}
	// The held swim inputs are cleared by their button release, not here: a swimmer bobbing at the surface
	// briefly leaves the water and must keep rising when it falls back in.
	if (IsUsingRide())
	{
		bSwimUpHeld = bSwimDownHeld = false;
	}
	else if (!bInWater || IsParkourTraversing())
	{
	}
	else if (Move->IsSwimming())
	{
		if (bSwimUpHeld) AddMovementInput(FVector::UpVector, 1.f);
		else if (bSwimDownHeld) AddMovementInput(FVector::DownVector, 1.f);
		else if (Water)
		{
			// Near the surface an idle swimmer floats with the head out; deeper down it settles to the bottom.
			const float Top = GetActorLocation().Z + HalfHeight;
			const float Surface = Water->GetSurfaceZ();
			const float Target = Top > Surface - 150.f
				? FMath::Clamp((Surface + 25.f - Top) * 1.5f, -150.f, 150.f)
				: -SeabedSinkSpeed;
			Move->Velocity.Z = FMath::FInterpTo(Move->Velocity.Z, Target, DeltaTime, 3.f);
		}

		// At the surface, swimming into a low ledge (a jetty, boarding float or bank lip) climbs out onto it.
		const FVector Push = Move->GetCurrentAcceleration().GetSafeNormal2D();
		ClimbOutCooldown = FMath::Max(0.f, ClimbOutCooldown - DeltaTime);
		if (Water && !bSubmerged && !Push.IsNearlyZero() && ClimbOutCooldown <= 0.f)
		{
			const float Surface = Water->GetSurfaceZ();
			const float Radius = GetCapsuleComponent()->GetScaledCapsuleRadius();
			const FVector Probe = GetActorLocation() + Push * (Radius + 45.f);
			FCollisionQueryParams Params(SCENE_QUERY_STAT(SwimClimbOut), false, this);
			FHitResult Ledge;
			if (GetWorld()->LineTraceSingleByChannel(Ledge, FVector(Probe.X, Probe.Y, Surface + 160.f), FVector(Probe.X, Probe.Y, Surface - 30.f), ECC_Visibility, Params)
				&& Ledge.ImpactNormal.Z >= Move->GetWalkableFloorZ()
				&& Ledge.ImpactPoint.Z > GetActorLocation().Z - HalfHeight + Move->MaxStepHeight)
			{
				const FVector Stand = Ledge.ImpactPoint + FVector(0.f, 0.f, HalfHeight + 5.f);
				if (!GetWorld()->OverlapBlockingTestByChannel(Stand, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Radius, HalfHeight), Params))
				{
					// Rise straight up first; the step forward onto the ledge follows once the feet clear it.
					const float Rise = FMath::Max(0.f, Stand.Z - GetActorLocation().Z) + 40.f;
					Move->SetMovementMode(MOVE_Falling);
					LaunchCharacter(FVector::UpVector * FMath::Sqrt(2.f * FMath::Abs(Move->GetGravityZ()) * Rise), true, true);
					bClimbingOut = true;
					ClimbOutLedgeZ = Ledge.ImpactPoint.Z;
					ClimbOutDirection = Push;
					ClimbOutCooldown = 0.75f;
					return;
				}
			}
		}

		// Settle onto the bottom (or wade out at a bank) when there is walkable ground right underfoot.
		if (!bSwimUpHeld && Move->Velocity.Z <= 10.f && (bSubmerged || Move->ImmersionDepth() < 0.6f))
		{
			FFindFloorResult Floor;
			Move->FindFloor(GetActorLocation(), Floor, false);
			if (Floor.IsWalkableFloor() && Floor.FloorDist < 25.f)
			{
				Move->SetMovementMode(MOVE_Walking);
			}
		}
	}
	else if (Move->IsMovingOnGround())
	{
		bSeabedWalking = bSubmerged;
		if (bSubmerged && bSwimUpHeld)
		{
			Move->SetMovementMode(MOVE_Swimming);
			Move->Velocity.Z = 220.f;
			bSeabedWalking = false;
		}
	}
	else if (Move->IsFalling() && bSubmerged)
	{
		// Swim inputs take over a fall; otherwise stepping off a ledge on the bottom sinks as a slow fall.
		if (bSwimUpHeld || bSwimDownHeld) Move->SetMovementMode(MOVE_Swimming);
		else bSeabedFalling = true;
	}

	if (bSeabedFalling && !(Move->IsFalling() && bSubmerged)) bSeabedFalling = false;
	if (bSeabedFalling && !bSeabedGravityApplied) { LandGravityScale = Move->GravityScale; Move->GravityScale *= 0.35f; bSeabedGravityApplied = true; }
	else if (!bSeabedFalling && bSeabedGravityApplied) { Move->GravityScale = LandGravityScale; bSeabedGravityApplied = false; }

	// Slow, heavy steps on the bottom; the land speed comes back on leaving it.
	if (bSeabedWalking && !bWasSeabed) LandWalkSpeed = Move->MaxWalkSpeed;
	if (bSeabedWalking) Move->MaxWalkSpeed = FMath::Min(SeabedWalkSpeed, LandWalkSpeed > 0.f ? LandWalkSpeed : SeabedWalkSpeed);
	else if (bWasSeabed && LandWalkSpeed > 0.f) Move->MaxWalkSpeed = LandWalkSpeed;
}

void ACarnivalPlayerCharacter::UpdateUnderwaterLook()
{
	if (!FollowCamera) return;
	const ACarnivalWaterVolume* Water = ACarnivalWaterVolume::FindAt(GetWorld(), FollowCamera->GetComponentLocation());
	bCameraUnderwater = Water && Water->bWaterVolume;
	if (bCameraUnderwater && !UnderwaterLookMaterial)
	{
		if (UMaterialInterface* Base = UnderwaterPostProcessMaterial.LoadSynchronous())
		{
			UnderwaterLookMaterial = UMaterialInstanceDynamic::Create(Base, this);
			FollowCamera->PostProcessSettings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, UnderwaterLookMaterial));
		}
	}
	if (bCameraUnderwater && UnderwaterLookMaterial)
	{
		UnderwaterLookMaterial->SetScalarParameterValue(TEXT("FogKeepPerMetre"), FMath::Exp(-Water->UnderwaterFogPerMetre));
		UnderwaterLookMaterial->SetVectorParameterValue(TEXT("FogColor"), Water->UnderwaterFogColor);
		UnderwaterLookMaterial->SetScalarParameterValue(TEXT("SurfaceZ"), Water->GetSurfaceZ());
	}
	FollowCamera->PostProcessBlendWeight = bCameraUnderwater ? 1.f : 0.f;
}

void ACarnivalPlayerCharacter::UpdateSwimAnimation()
{
	UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!Anim) return;
	UAnimSequence* Wanted = nullptr;
	if (GetCharacterMovement()->IsSwimming() && !IsUsingRide())
	{
		const FVector Local = GetActorRotation().UnrotateVector(FVector(GetVelocity().X, GetVelocity().Y, 0.f));
		if (Local.Size2D() < 40.f) Wanted = SwimIdleAnimation.LoadSynchronous();
		else if (FMath::Abs(Local.Y) > FMath::Abs(Local.X) * 1.2f) Wanted = (Local.Y > 0.f ? SwimRightAnimation : SwimLeftAnimation).LoadSynchronous();
		else Wanted = SwimForwardAnimation.LoadSynchronous();
	}
	if (Wanted == ActiveSwimSequence && (!Wanted || (ActiveSwimMontage && Anim->Montage_IsPlaying(ActiveSwimMontage)))) return;
	if (ActiveSwimMontage && Anim->Montage_IsPlaying(ActiveSwimMontage)) Anim->Montage_Stop(0.25f, ActiveSwimMontage);
	ActiveSwimSequence = Wanted;
	ActiveSwimMontage = Wanted ? Anim->PlaySlotAnimationAsDynamicMontage(Wanted, SwimSlotName, 0.25f, 0.25f, 1.f, 100000) : nullptr;
}

ACarnivalMissionInteractionActor* ACarnivalPlayerCharacter::FindNearbyMissionInteraction() const
{
	ACarnivalMissionInteractionActor* Closest = nullptr;
	float BestDistanceSquared = TNumericLimits<float>::Max();
	for (TActorIterator<ACarnivalMissionInteractionActor> It(GetWorld()); It; ++It)
	{
		if (!It->CanInteract(this)) continue;
		const float DistanceSquared = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
		if (DistanceSquared < BestDistanceSquared)
		{
			BestDistanceSquared = DistanceSquared;
			Closest = *It;
		}
	}
	return Closest;
}

void ACarnivalPlayerCharacter::OnMountMotorcycle(ACarnivalMotorcycle* Bike, bool bMountLeft)
{
	if (!Bike)
	{
		return;
	}

	MountedMotorcycle = Bike;
	SetLocomotionState(ECarnivalLocomotionState::RidingMotorcycle);

	// Disable character physics & collision while mounted
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetCharacterMovement()->DisableMovement();

	// Play mount montage
	UAnimMontage* MountMontage = bMountLeft ? MountLeftMontage : MountRightMontage;
	if (MountMontage)
	{
		PlayAnimMontage(MountMontage);
	}

	// Attach to bike seat
	AttachToComponent(Bike->GetRootComponent(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, Bike->DriverSeatSocketName);
}

void ACarnivalPlayerCharacter::OnDismountMotorcycle(ACarnivalMotorcycle* Bike, bool bDismountLeft)
{
	// Stop riding montage
	if (RidingIdleMontage)
	{
		StopAnimMontage(RidingIdleMontage);
	}

	// Detach and restore collision
	DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);

	// The motorcycle has already staged the dismount animation before
	// restoring walking. Do not restart it from a seated pose at the exit.

	MountedMotorcycle = nullptr;
	SetLocomotionState(ECarnivalLocomotionState::Jogging);
}

void ACarnivalPlayerCharacter::OnMountBoat(ACarnivalBoat* Boat)
{
	if (!Boat) return;
	MountedBoat = Boat;
	SetLocomotionState(ECarnivalLocomotionState::DrivingBoat);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetCharacterMovement()->DisableMovement();
	AttachToComponent(Boat->GetRootComponent(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, Boat->DriverSeatSocketName);
	SetActorRelativeLocation(Boat->DriverRelativeOffset);
}

void ACarnivalPlayerCharacter::OnDismountBoat()
{
	DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	if (GetCharacterMovement()->IsInWater())
	{
		GetCharacterMovement()->SetMovementMode(MOVE_Swimming);
		SetLocomotionState(ECarnivalLocomotionState::Swimming);
	}
	else
	{
		GetCharacterMovement()->SetMovementMode(MOVE_Walking);
		SetLocomotionState(ECarnivalLocomotionState::Jogging);
	}
	MountedBoat = nullptr;
}

void ACarnivalPlayerCharacter::OnMountHovercraft(ACarnivalHovercraft* Craft)
{
	if (!Craft) return;
	MountedHovercraft = Craft;
	SetLocomotionState(ECarnivalLocomotionState::PilotingHovercraft);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetCharacterMovement()->DisableMovement();
	AttachToComponent(Craft->GetRootComponent(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, Craft->DriverSeatSocketName);
	SetActorRelativeLocation(Craft->DriverRelativeOffset);
}

void ACarnivalPlayerCharacter::OnDismountHovercraft()
{
	DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	SetLocomotionState(ECarnivalLocomotionState::Jogging);
	MountedHovercraft = nullptr;
}

void ACarnivalPlayerCharacter::PerformMountedAttack(bool bIsShooting, bool bPunchRight)
{
	if (bIsShooting)
	{
		if (MountedShootMontage)
		{
			PlayAnimMontage(MountedShootMontage);
		}
		if (CurrentWeapon)
		{
			CurrentWeapon->PerformAttack(this);
		}
	}
	else
	{
		UAnimMontage* PunchMontage = bPunchRight ? MountedPunchRightMontage : MountedPunchLeftMontage;
		if (!PunchMontage)
		{
			PunchMontage = UnarmedPunchMontage;
		}
		if (PunchMontage)
		{
			PlayAnimMontage(PunchMontage);
		}
	}
}

void ACarnivalPlayerCharacter::EquipWeaponSlot(int32 SlotIndex)
{
	if (IsParkourTraversing()) return;
	TSubclassOf<ACarnivalWeaponBase> TargetClass = nullptr;

	switch (SlotIndex)
	{
	case 1:
		TargetClass = DefaultSwordClass;
		break;
	case 2:
		TargetClass = DefaultRevolverClass;
		break;
	case 3:
		TargetClass = DefaultKnifeClass;
		break;
	default:
		// Unarmed
		if (CurrentWeapon)
		{
			CurrentWeapon->Destroy();
			CurrentWeapon = nullptr;
		}
		return;
	}

	if (TargetClass)
	{
		if (CurrentWeapon)
		{
			CurrentWeapon->Destroy();
			CurrentWeapon = nullptr;
		}

		FActorSpawnParameters SpawnParams;
		SpawnParams.Owner = this;
		SpawnParams.Instigator = this;

		CurrentWeapon = GetWorld()->SpawnActor<ACarnivalWeaponBase>(TargetClass, GetActorTransform(), SpawnParams);
		if (CurrentWeapon)
		{
			CurrentWeapon->AttachToCharacter(this, true);
		}
	}
}

void ACarnivalPlayerCharacter::PerformAttack()
{
	if (IsParkourTraversing() || IsUsingRide()) return;
	if (CurrentWeapon)
	{
		CurrentWeapon->PerformAttack(this);
	}
	else
	{
		if (GetWorld()->GetTimeSeconds() < NextUnarmedAttackTime) return;
		NextUnarmedAttackTime = GetWorld()->GetTimeSeconds() + .5;
		FVector Start; FRotator Aim;
		GetActorEyesViewPoint(Start, Aim);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalUnarmedAttack), false, this);
		FHitResult Hit;
		if (GetWorld()->SweepSingleByChannel(Hit, Start, Start + Aim.Vector() * 160.f, FQuat::Identity,
			ECC_Visibility, FCollisionShape::MakeSphere(25.f), Params) && IsValid(Hit.GetActor()))
		{
			UGameplayStatics::ApplyPointDamage(Hit.GetActor(), 25.f, Aim.Vector(), Hit, GetController(), this, nullptr);
		}
		// Alternate per character, without sharing state with NPCs or other players.
		UAnimMontage* Montage = bPunchNext ? UnarmedPunchMontage : UnarmedKickMontage;
		if (Montage)
		{
			PlayAnimMontage(Montage);
		}
		bPunchNext = !bPunchNext;
	}
}

void ACarnivalPlayerCharacter::MoveForward(float Value)
{
	if (IsParkourTraversing()) return;
    if (IsUsingRide()) return;
	if ((Controller != nullptr) && (Value != 0.0f) && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		const FRotator Rotation = Controller->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);
		// Fully under water, forward follows the camera pitch so looking down dives.
		const bool bPitchSwim = GetCharacterMovement()->IsSwimming() && bSubmerged
			&& FMath::Abs(FRotator::NormalizeAxis(Rotation.Pitch)) > 20.f;
		const FVector Direction = bPitchSwim ? Rotation.Vector() : FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
		AddMovementInput(Direction, Value);
	}
}

void ACarnivalPlayerCharacter::MoveRight(float Value)
{
	if (IsParkourTraversing()) return;
    if (IsUsingRide()) return;
	if ((Controller != nullptr) && (Value != 0.0f) && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		const FRotator Rotation = Controller->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);
		const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
		AddMovementInput(Direction, Value);
	}
}

void ACarnivalPlayerCharacter::TurnAtRate(float Rate)
{
	AddControllerYawInput(Rate * 45.f * GetWorld()->GetDeltaSeconds());
}

void ACarnivalPlayerCharacter::LookUpAtRate(float Rate)
{
	AddControllerPitchInput(Rate * 45.f * GetWorld()->GetDeltaSeconds());
}

void ACarnivalPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
}

bool ACarnivalPlayerCharacter::IsUsingRide() const
{
    return (RidePassenger && RidePassenger->IsRiding()) || IsValid(OperatingRide);
}

ACarnivalRideAttendant* ACarnivalPlayerCharacter::FindNearbyAttendant() const
{
    ACarnivalRideAttendant* Closest = nullptr;
    float Best = FLT_MAX;
    for (TActorIterator<ACarnivalRideAttendant> It(GetWorld()); It; ++It)
    {
        if (!It->Operation || !It->Operation->IsInInteractionRange(const_cast<ACarnivalPlayerCharacter*>(this))) continue;
        const float Distance = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
        if (Distance < Best) { Best = Distance; Closest = *It; }
    }
    return Closest;
}

void ACarnivalPlayerCharacter::InteractWithRideOperator()
{
	if (IsParkourTraversing()) return;
    if (OperatingRide) { LeaveRideOperator(); return; }
    if (RidePassenger->IsRiding()) return;
    if (auto* Attendant = FindNearbyAttendant())
    {
        if (Attendant->Operation->TakeOperatorControl(this))
        {
            OperatingRide = Attendant->Operation;
            GetCharacterMovement()->StopMovementImmediately();
            GetCharacterMovement()->DisableMovement();
        }
    }
}

void ACarnivalPlayerCharacter::LeaveRideOperator()
{
    if (!OperatingRide) return;
    if (IsValid(OperatingRide)) OperatingRide->ReleaseOperatorControl(this);
    OperatingRide = nullptr;
    GetCharacterMovement()->SetMovementMode(MOVE_Walking);
}

void ACarnivalPlayerCharacter::HandleRideBoarded(AActor* RideActor, UCarnivalRideSeatComponent* Seat)
{
    PreRideCameraLength = CameraBoom->TargetArmLength;
    CameraBoom->TargetArmLength = 200.f;
    PreRideAnimationMode = GetMesh()->GetAnimationMode();
    PreRideAnimClass = GetMesh()->GetAnimClass();
    if (RideSeatedAnimation && (!Seat || !Seat->bStandingPassenger))
    {
        GetMesh()->PlayAnimation(RideSeatedAnimation, true);
    }
}

void ACarnivalPlayerCharacter::HandleRideUnboarded(AActor* RideActor)
{
    CameraBoom->TargetArmLength = PreRideCameraLength;
    if (RideSeatedAnimation)
    {
        GetMesh()->SetAnimationMode(static_cast<EAnimationMode::Type>(PreRideAnimationMode));
        if (PreRideAnimClass) GetMesh()->SetAnimInstanceClass(PreRideAnimClass);
    }
    SetLocomotionState(ECarnivalLocomotionState::Jogging);
}
