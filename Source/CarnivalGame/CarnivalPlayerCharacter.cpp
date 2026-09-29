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
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Components/CapsuleComponent.h"

ACarnivalPlayerCharacter::ACarnivalPlayerCharacter()
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
    if (OperatingRide && (!IsValid(OperatingRide) || OperatingRide->PlayerOperator != this))
    {
        OperatingRide = nullptr;
        GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    }
    if (IsUsingRide())
    {
        BlockedInputDuration = SwimmingDuration = FallingDuration = 0.f;
        return;
    }

	UpdateSafeRecoveryState(DeltaTime);

	// Update movement state based on movement component
	if (LocomotionState != ECarnivalLocomotionState::RidingMotorcycle &&
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
	SwimmingDuration = bSwimming ? SwimmingDuration + DeltaTime : 0.f;
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

bool ACarnivalPlayerCharacter::FindSafeRecoveryLocation(FVector& OutLocation) const
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
		const FVector Sample = LastSafeRecoveryLocation + Offset;
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
		if (GetWorld()->OverlapBlockingTestByChannel(Candidate, LastSafeRecoveryRotation.Quaternion(), ECC_Pawn,
			StandingCapsule, QueryParams))
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

	if (bIsCrouched) UnCrouch();
	bIsProne = false;
	GetCapsuleComponent()->SetCapsuleSize(DefaultCapsuleRadius, DefaultCapsuleHalfHeight, true);
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -DefaultCapsuleHalfHeight));
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	ConsumeMovementInputVector();

	const bool bMoved = SetActorLocationAndRotation(RecoveryLocation, LastSafeRecoveryRotation,
		false, nullptr, ETeleportType::TeleportPhysics);
	if (!bMoved) return false;

	SetLocomotionState(ECarnivalLocomotionState::Jogging);
	GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
	BlockedInputDuration = SwimmingDuration = FallingDuration = 0.f;
	LastSafeRecoveryLocation = RecoveryLocation;
	LastSafeRecoveryRotation = FRotator(0.f, GetActorRotation().Yaw, 0.f);
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
    if (IsUsingRide()) return;
	if (!bIsCrouched && !bIsProne && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		GetCharacterMovement()->MaxWalkSpeed = SprintSpeed;
		LocomotionState = ECarnivalLocomotionState::Sprinting;
	}
}

void ACarnivalPlayerCharacter::StopSprinting()
{
	if (!bIsCrouched && !bIsProne && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
		LocomotionState = ECarnivalLocomotionState::Jogging;
	}
}

void ACarnivalPlayerCharacter::ToggleCrouch()
{
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
    if (IsUsingRide()) return;
	if (bIsProne)
	{
		// Exit prone to stand
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
		}
		bIsProne = true;
		LocomotionState = ECarnivalLocomotionState::Prone;
		GetCapsuleComponent()->SetCapsuleSize(DefaultCapsuleRadius, 30.0f);
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
    if (IsUsingRide()) return false;
	if (LocomotionState == ECarnivalLocomotionState::RidingMotorcycle)
	{
		return false;
	}

	FVector Start = GetActorLocation();
	FVector Forward = GetActorForwardVector();
	FVector ChestStart = Start + FVector(0.0f, 0.0f, 20.0f);
	FVector ChestEnd = ChestStart + Forward * 130.0f;

	FHitResult WallHit;
	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);

	if (GetWorld()->LineTraceSingleByChannel(WallHit, ChestStart, ChestEnd, ECC_WorldStatic, Params))
	{
		// Find obstacle height
		FVector TraceTopDownStart = WallHit.ImpactPoint + Forward * 20.0f + FVector(0.0f, 0.0f, 150.0f);
		FVector TraceTopDownEnd = TraceTopDownStart - FVector(0.0f, 0.0f, 200.0f);
		FHitResult HeightHit;

		if (GetWorld()->LineTraceSingleByChannel(HeightHit, TraceTopDownStart, TraceTopDownEnd, ECC_WorldStatic, Params))
		{
			float ObstacleHeight = HeightHit.ImpactPoint.Z - (Start.Z - DefaultCapsuleHalfHeight);

			// Vault check (waist-high and thin)
			if (ObstacleHeight > 40.0f && ObstacleHeight <= 115.0f && VaultMontage)
			{
				SetLocomotionState(ECarnivalLocomotionState::Vaulting);
				PlayAnimMontage(VaultMontage);
				return true;
			}
			// 1M Mantle check
			else if (ObstacleHeight > 115.0f && ObstacleHeight <= 170.0f && Mantle1MMontage)
			{
				SetLocomotionState(ECarnivalLocomotionState::Mantling);
				PlayAnimMontage(Mantle1MMontage);
				return true;
			}
			// 2M Mantle check
			else if (ObstacleHeight > 170.0f && ObstacleHeight <= 230.0f && Mantle2MMontage)
			{
				SetLocomotionState(ECarnivalLocomotionState::Mantling);
				PlayAnimMontage(Mantle2MMontage);
				return true;
			}
		}
	}

	return false;
}

bool ACarnivalPlayerCharacter::TryLadderClimb()
{
	// Ladder trace logic
	return false;
}

void ACarnivalPlayerCharacter::TryInteractOrMount()
{
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
		ActiveActivity = NearbyActivity;
		return;
	}
	InteractWithRideOperator();
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
	if (CurrentWeapon)
	{
		CurrentWeapon->PerformAttack(this);
	}
	else
	{
		// Alternate unarmed punch and kick
		static bool bPunchNext = true;
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
    if (IsUsingRide()) return;
	if ((Controller != nullptr) && (Value != 0.0f) && LocomotionState != ECarnivalLocomotionState::RidingMotorcycle)
	{
		const FRotator Rotation = Controller->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);
		const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
		AddMovementInput(Direction, Value);
	}
}

void ACarnivalPlayerCharacter::MoveRight(float Value)
{
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
    if (RideSeatedAnimation)
    {
        PreRideAnimationMode = GetMesh()->GetAnimationMode();
        PreRideAnimClass = GetMesh()->GetAnimClass();
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
