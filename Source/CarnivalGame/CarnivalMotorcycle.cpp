// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalMotorcycle.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "NiagaraComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "Engine/SkeletalMesh.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "DrawDebugHelpers.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "TimerManager.h"

namespace
{
struct FArcadeChassisBox
{
	FVector Center;
	FQuat Rotation;
	FVector Extent;
};
using FChassisBoxes = TArray<FArcadeChassisBox, TInlineAllocator<4>>;

void GetChassisBoxes(const USkeletalMeshComponent* Mesh, FChassisBoxes& Boxes)
{
	if (const UPhysicsAsset* Physics = Mesh->GetPhysicsAsset())
	{
		for (const USkeletalBodySetup* Body : Physics->SkeletalBodySetups)
		{
			if (!Body) continue;
			const int32 Bone = Mesh->GetBoneIndex(Body->BoneName);
			if (Bone == INDEX_NONE) continue;
			const FTransform BoneWorld = Mesh->GetBoneTransform(Bone);
			for (const FKBoxElem& Box : Body->AggGeom.BoxElems)
			{
				const FTransform ShapeWorld = FTransform(Box.Rotation, Box.Center) * BoneWorld;
				Boxes.Add({ShapeWorld.GetLocation(), ShapeWorld.GetRotation(),
					FVector(Box.X, Box.Y, Box.Z) * .5f * ShapeWorld.GetScale3D().GetAbs()});
			}
		}
	}
	if (Boxes.IsEmpty() && Mesh->GetSkeletalMeshAsset())
	{
		const FBoxSphereBounds Bounds = Mesh->GetSkeletalMeshAsset()->GetBounds();
		const FTransform Transform = Mesh->GetComponentTransform();
		Boxes.Add({Transform.TransformPosition(Bounds.Origin), Transform.GetRotation(), Bounds.BoxExtent * Transform.GetScale3D().GetAbs()});
	}
}
}

ACarnivalMotorcycle::ACarnivalMotorcycle()
{
	PrimaryActorTick.bCanEverTick = true;

	BikeMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("BikeMesh"));
	SetRootComponent(BikeMesh);
	BikeMesh->SetCollisionProfileName(TEXT("Vehicle"));

	FrontWheel = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FrontWheel"));
	FrontWheel->SetupAttachment(BikeMesh);
	FrontWheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	RearWheel = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RearWheel"));
	RearWheel->SetupAttachment(BikeMesh);
	RearWheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);

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

void ACarnivalMotorcycle::Destroyed()
{
	RecoverMountedRider(true);
	Super::Destroyed();
}

void ACarnivalMotorcycle::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (bDismounting)
	{
		BlockedDriveDuration = 0.f;
		CurrentSpeed = 0.f;
		UpdateDismount();
		return;
	}
	const FVector BeforeMove = GetActorLocation();

	if (PhysicsMode == EMotorcyclePhysicsMode::Arcade)
	{
		UpdateArcadePhysics(DeltaTime);
	}
	else
	{
		UpdateChaosPhysics(DeltaTime);
	}
	const FVector Heading = FRotator(0.f, GetActorRotation().Yaw, 0.f).Vector();
	const float Distance = FVector::DotProduct(GetActorLocation() - BeforeMove, Heading);
	WheelSpinDegrees = FMath::Fmod(WheelSpinDegrees + FMath::RadiansToDegrees(Distance / FMath::Max(WheelRadius, 1.f)), 360.f);
	FrontWheel->SetRelativeRotation(FRotator(-WheelSpinDegrees, SteeringInput * 28.f, 0.f));
	RearWheel->SetRelativeRotation(FRotator(-WheelSpinDegrees, 0.f, 0.f));

	const float MovementDistance = FVector::Distance(BeforeMove, GetActorLocation());
	const bool bDriverRequestsMovement = CurrentRider
		&& (FMath::Abs(ThrottleInput) > .2f || BrakeReverseInput > .2f);
	const bool bMotionIsBlocked = PhysicsMode == EMotorcyclePhysicsMode::Arcade
		? LastMovementHit.bBlockingHit
		: FMath::Abs(CurrentSpeed) < 50.f;
	if (bDriverRequestsMovement && !bIsAirborne && MovementDistance < 1.f && bMotionIsBlocked)
	{
		BlockedDriveDuration += DeltaTime;
	}
	else if (!bDriverRequestsMovement || bIsAirborne || MovementDistance >= 1.f)
	{
		BlockedDriveDuration = 0.f;
	}
}

void ACarnivalMotorcycle::UpdateArcadePhysics(float DeltaTime)
{
	const UAnimMontage* RiderMontage = CurrentRider ? CurrentRider->GetCurrentMontage() : nullptr;
	const bool bMounting = RiderMontage && (RiderMontage == CurrentRider->MountLeftMontage
		|| RiderMontage == CurrentRider->MountRightMontage);
	// Acceleration and Braking
	if (bMounting)
	{
		// Keep the chassis still while the rider's supporting foot is moving
		// from the ground to the peg. Held inputs resume after the idle handoff.
		CurrentSpeed = 0.f;
	}
	else if (BrakeInput > 0.01f || bHandbrake)
	{
		const float BrakeStrength = FMath::Max(BrakeInput, bHandbrake ? .55f : 0.f);
		CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, 0.f, DeltaTime,
			BrakingDeceleration * BrakeStrength);
	}
	else if (BrakeReverseInput > .01f)
	{
		// L2 brakes forward travel to a complete stop before backing up.
		// Opposing triggers hold the bike stopped; reverse propulsion requires
		// ground support and never changes the direction of an airborne bike.
		if (CurrentSpeed > .01f || ThrottleInput > .01f || bIsAirborne)
			CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, 0.f, DeltaTime, BrakingDeceleration * BrakeReverseInput);
		else
			CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, -ReverseSpeed * BrakeReverseInput, DeltaTime, Acceleration * BrakeReverseInput);
	}
	else if (ThrottleInput > 0.01f)
	{
		CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, MaxSpeed * ThrottleInput, DeltaTime, Acceleration);
	}
	else if (ThrottleInput < -0.01f)
	{
		CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, -ReverseSpeed * FMath::Abs(ThrottleInput), DeltaTime, Acceleration);
	}
	else
	{
		// Coasting friction
		CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, 0.0f, DeltaTime, 400.0f);
	}

	// Steering and Yaw rotation
	float SpeedRatio = FMath::Clamp(FMath::Abs(CurrentSpeed) / MaxSpeed, 0.0f, 1.0f);
	if (FMath::Abs(CurrentSpeed) > 10.0f)
	{
		float DirectionMultiplier = (CurrentSpeed >= 0.0f) ? 1.0f : -1.0f;
		// Strong low-speed turning, progressively calmer at speed. Rear brake
		// permits a tighter pivot while momentum keeps its previous direction.
		const float SteeringAuthority = FMath::Lerp(1.f, .45f, SpeedRatio)
			* FMath::Clamp(FMath::Abs(CurrentSpeed) / 150.f, 0.f, 1.f);
		float YawDelta = SteeringInput * TurnRate * DirectionMultiplier * DeltaTime
			* SteeringAuthority * (bIsAirborne ? .35f : (bHandbrake ? 1.5f : 1.f));
		AddActorWorldRotation(FRotator(0.0f, YawDelta, 0.0f));
	}

	// Dynamic Leaning
	float TargetLean = bMounting ? 0.f : -SteeringInput * MaxLeanAngle * SpeedRatio;
	CurrentLean = FMath::FInterpTo(CurrentLean, TargetLean, DeltaTime, 6.0f);

	// Forward movement
	const float HeadingYaw = GetActorRotation().Yaw;
	if (!bHasTravelHeading || FMath::Abs(CurrentSpeed) < 10.f)
	{
		TravelYaw = HeadingYaw;
		bHasTravelHeading = true;
	}
	if (!bIsAirborne)
	{
		const float Grip = bHandbrake ? 1.6f : 14.f;
		TravelYaw += FMath::FindDeltaAngleDegrees(TravelYaw, HeadingYaw) * (1.f - FMath::Exp(-Grip * DeltaTime));
	}
	SlipAngle = FMath::FindDeltaAngleDegrees(TravelYaw, HeadingYaw);
	// Pitch is rider attitude, not extra vertical propulsion. Gravity and
	// ground contact alone update altitude, so wheelies cannot become flight.
	FVector ForwardMove = FRotator(0.f, TravelYaw, 0.f).Vector() * CurrentSpeed * DeltaTime;
	if (!bIsAirborne && LastGroundNormal.Z > .7f)
	{
		// Sweep along the support plane instead of pushing the body box into
		// an uphill surface and correcting its height only after collision.
		ForwardMove.Z = -FVector::DotProduct(LastGroundNormal, ForwardMove) / LastGroundNormal.Z;
	}
	FHitResult SweepHit;
	if (const USkeletalMesh* Mesh = BikeMesh->GetSkeletalMeshAsset())
	{
		// Sweep authored chassis volumes in their actual bone/world transforms.
		// A narrow lower frame avoids a false floor hit beneath wide handlebars.
		FChassisBoxes Chassis;
		GetChassisBoxes(BikeMesh, Chassis);
		FCollisionQueryParams MoveParams(SCENE_QUERY_STAT(MotorcycleBody), false, this);
		if (CurrentRider) MoveParams.AddIgnoredActor(CurrentRider);
		const FCollisionShape TyreShape = FCollisionShape::MakeSphere(FMath::Max(1.f, WheelRadius - .25f));
		const FCollisionResponseParams Responses(BikeMesh->GetCollisionResponseToChannels());
		// The tyres extend beyond the body. Rounded axle sweeps catch walls
		// before the visible wheel enters them; a small skin avoids resting
		// contact with the floor blocking horizontal travel.
		auto SweepVehicle = [&](FVector Offset, FVector Delta, FHitResult& Result)
		{
			Result = FHitResult();
			for (const FArcadeChassisBox& Box : Chassis)
			{
				FHitResult BodyHit;
				GetWorld()->SweepSingleByChannel(BodyHit, Box.Center + Offset, Box.Center + Offset + Delta, Box.Rotation,
					BikeMesh->GetCollisionObjectType(), FCollisionShape::MakeBox(Box.Extent), MoveParams, Responses);
				if (BodyHit.bBlockingHit && (!Result.bBlockingHit || BodyHit.Time < Result.Time)) Result = BodyHit;
			}
			for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
			{
				if (!Wheel->GetStaticMesh()) continue;
				FHitResult WheelHit;
				const FVector Axle = Wheel->GetComponentLocation() + Offset;
				GetWorld()->SweepSingleByChannel(WheelHit, Axle, Axle + Delta, FQuat::Identity,
					BikeMesh->GetCollisionObjectType(), TyreShape, MoveParams, Responses);
				if (WheelHit.bBlockingHit && FMath::Abs(WheelHit.ImpactNormal.Z) < .7f
					&& (!Result.bBlockingHit || WheelHit.Time < Result.Time)) Result = WheelHit;
			}
		};
		SweepVehicle(FVector::ZeroVector, ForwardMove, SweepHit);
		if (SweepHit.bBlockingHit && !SweepHit.bStartPenetrating && !bIsAirborne && MaxStepHeight > 0.f)
		{
			// A tyre can roll onto a low curb. Require support at the destination
			// and clear upward/forward sweeps; a tall wall or low ceiling remains
			// blocking rather than being bypassed by a vertical teleport.
			float Lift = 0.f;
			for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
			{
				if (!Wheel->GetStaticMesh()) continue;
				const FVector Destination = Wheel->GetComponentLocation() + ForwardMove;
				FHitResult Support;
				if (GetWorld()->SweepSingleByChannel(Support, Destination + FVector(0,0,MaxStepHeight + 1.f),
					Destination - FVector(0,0,1), FQuat::Identity, ECC_WorldStatic, TyreShape, MoveParams)
					&& !Support.bStartPenetrating && Support.ImpactNormal.Z > .1f)
					Lift = FMath::Max(Lift, float(Support.Location.Z + .25f - Destination.Z));
			}
			if (Lift > .01f && Lift <= MaxStepHeight)
			{
				FHitResult UpHit, AcrossHit;
				const FVector Up(0,0,Lift);
				SweepVehicle(FVector::ZeroVector, Up, UpHit);
				SweepVehicle(Up, ForwardMove, AcrossHit);
				if (!UpHit.bBlockingHit && !AcrossHit.bBlockingHit)
				{
					ForwardMove += Up;
					SweepHit = FHitResult();
				}
			}
		}
		AddActorWorldOffset(ForwardMove * (SweepHit.bBlockingHit ? SweepHit.Time : 1.f), false);
		if (SweepHit.bBlockingHit && FMath::Abs(SweepHit.ImpactNormal.Z) < .7f)
			CurrentSpeed = 0.f;
	}
	else
	{
		AddActorWorldOffset(ForwardMove, true, &SweepHit);
	}
	LastMovementHit = SweepHit;

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

	const bool bHit = GetWorld()->LineTraceSingleByChannel(GroundHit, StartTrace, EndTrace, ECC_WorldStatic, Params);
	const bool bCloseToGround = bHit && GetActorLocation().Z - GroundHit.ImpactPoint.Z <= 5.f;
	if (bHit && VerticalVelocity <= 0.0f && (!bIsAirborne || bCloseToGround))
	{
		// Smoothly position onto ground
		float TargetZ = GroundHit.ImpactPoint.Z;
		FVector NewLoc = GetActorLocation();
		NewLoc.Z = FMath::FInterpTo(NewLoc.Z, TargetZ, DeltaTime, 12.0f);
		SetActorLocation(NewLoc);

		// Align roll with leaning and pitch with ground slope
		FRotator CurrentRot = GetActorRotation();
		FVector Normal = GroundHit.ImpactNormal;
		LastGroundNormal = Normal;
		// Project the ground slope along the bike's heading. An upward normal's
		// orientation has a 90-degree pitch, so adding 90 inverted a level bike.
		const FVector Heading = FRotator(0.0f, CurrentRot.Yaw, 0.0f).Vector();
		const float TargetPitch = FMath::RadiansToDegrees(FMath::Atan2(
			-FVector::DotProduct(Normal, Heading), FMath::Max(Normal.Z, 0.001)));
		

		// Launch off ramp if speeding off an upward slope
		const bool bWasAirborne = bIsAirborne;
		bIsAirborne = false;
		VerticalVelocity = 0.0f;
		if (!bWasAirborne && TargetPitch > 8.0f && CurrentSpeed > 350.0f)
		{
			FVector FrontStart = GetActorLocation() + FRotator(TargetPitch, CurrentRot.Yaw, 0.f).Vector() * 160.0f + FVector(0.0f, 0.0f, 50.0f);
			FVector FrontEnd = FrontStart - FVector(0.0f, 0.0f, 150.0f);
			FHitResult FrontHit;
			if (!GetWorld()->LineTraceSingleByChannel(FrontHit, FrontStart, FrontEnd, ECC_WorldStatic, Params))
			{
				bIsAirborne = true;
				VerticalVelocity = CurrentSpeed * FMath::Sin(FMath::DegreesToRadians(TargetPitch)) * 1.3f;
			}
		}

		const float WheelieTarget = !bMounting && !bHandbrake && BrakeInput < .01f && BrakeReverseInput < .01f && ThrottleInput > .1f
			&& CurrentSpeed > 200.f ? FMath::Max(RiderBalanceInput, 0.f) * MaxWheelieAngle : 0.f;
		WheelieAngle = FMath::FInterpConstantTo(WheelieAngle, WheelieTarget, DeltaTime, 65.f);
		FRotator TargetRot(TargetPitch + WheelieAngle, CurrentRot.Yaw, CurrentLean);
		SetActorRotation(FMath::RInterpTo(CurrentRot, TargetRot, DeltaTime, 8.0f));
		if (BikeMesh->GetSkeletalMeshAsset() && FrontWheel->GetStaticMesh() && RearWheel->GetStaticMesh())
		{
			// Keep the supporting tyre on the surface as pitch/lean changes.
			// Rotating around the actor origin alone drove the rear tyre below
			// ground during a wheelie. Root lift here is contact geometry, not
			// upward velocity or an airborne launch.
			const FVector Origin = GetActorLocation();
			const float RearSupport = WheelRadius - FVector::DotProduct(Normal, RearWheel->GetComponentLocation() - Origin);
			const float FrontSupport = WheelRadius - FVector::DotProduct(Normal, FrontWheel->GetComponentLocation() - Origin);
			FVector SupportedLocation = Origin;
			SupportedLocation.Z = GroundHit.ImpactPoint.Z + FMath::Max(RearSupport, FrontSupport) / FMath::Max(Normal.Z, .001);
			// At a pavement edge the centre ray can reach the lower road before
			// the rear tyre leaves the upper surface. Rounded downward probes
			// retain that support until the wheel rolls clear of the edge.
			for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
			{
				const FVector Axle = Wheel->GetComponentLocation();
				FHitResult Contact;
				if (GetWorld()->SweepSingleByChannel(Contact, Axle + FVector(0,0,120), Axle - FVector(0,0,200),
					FQuat::Identity, ECC_WorldStatic, FCollisionShape::MakeSphere(FMath::Max(1.f, WheelRadius - .25f)), Params)
					&& Contact.ImpactNormal.Z > .35f && !Contact.bStartPenetrating)
				{
					SupportedLocation.Z = FMath::Max(SupportedLocation.Z, Contact.Location.Z + .25f - (Axle.Z - Origin.Z));
				}
			}
			// Support correction must also respect headroom for the chassis.
			// Allow recovery out of an initial floor overlap only if the target
			// body volume is clear; do not lift through a low roof at a curb.
			const FVector Correction = SupportedLocation - Origin;
			const FCollisionResponseParams Responses(BikeMesh->GetCollisionResponseToChannels());
			FChassisBoxes Chassis;
			GetChassisBoxes(BikeMesh, Chassis);
			bool bClear = true;
			for (const FArcadeChassisBox& Box : Chassis)
			{
				const FCollisionShape Shape = FCollisionShape::MakeBox(Box.Extent);
				FHitResult SupportSweep;
				GetWorld()->SweepSingleByChannel(SupportSweep, Box.Center, Box.Center + Correction, Box.Rotation,
					BikeMesh->GetCollisionObjectType(), Shape, Params, Responses);
				const bool bRecovering = SupportSweep.bStartPenetrating && FVector::DotProduct(Correction, SupportSweep.Normal) > 0.f;
				const bool bTargetBlocked = GetWorld()->OverlapBlockingTestByChannel(Box.Center + Correction, Box.Rotation,
					BikeMesh->GetCollisionObjectType(), Shape, Params, Responses);
				bClear &= !bTargetBlocked && (!SupportSweep.bBlockingHit || bRecovering);
			}
			if (bClear) SetActorLocation(SupportedLocation);
			else if (Correction.Z > .01f) CurrentSpeed = 0.f;
		}
	}
	else
	{
		// Ballistic flight, with continuous collision over the vertical step.
		bIsAirborne = true;
		VerticalVelocity -= 980.0f * DeltaTime; // Gravity

		// Orient towards flight path
		FRotator CurrentRot = GetActorRotation();
		WheelieAngle = 0.f;
		const float NeutralPitch = FMath::Clamp(VerticalVelocity * .03f, -35.f, 35.f);
		const float Pitch = FMath::Abs(RiderBalanceInput) > .01f
			? CurrentRot.Pitch + RiderBalanceInput * AirPitchRate * DeltaTime
			: FMath::FInterpTo(CurrentRot.Pitch, NeutralPitch, DeltaTime, 1.5f);
		SetActorRotation(FRotator(FMath::Clamp(Pitch, -65.f, 65.f), CurrentRot.Yaw,
			FMath::FInterpTo(CurrentRot.Roll, CurrentLean * .5f, DeltaTime, 4.f)));
		const FCollisionResponseParams Responses(BikeMesh->GetCollisionResponseToChannels());
		const FCollisionShape TyreShape = FCollisionShape::MakeSphere(FMath::Max(1.f, WheelRadius - .25f));
		FChassisBoxes Chassis;
		GetChassisBoxes(BikeMesh, Chassis);
		bool bRotationBlocked = false;
		for (const FArcadeChassisBox& Box : Chassis)
			bRotationBlocked |= GetWorld()->OverlapBlockingTestByChannel(Box.Center, Box.Rotation,
				BikeMesh->GetCollisionObjectType(), FCollisionShape::MakeBox(Box.Extent), Params, Responses);
		for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
			if (Wheel->GetStaticMesh()) bRotationBlocked |= GetWorld()->OverlapBlockingTestByChannel(Wheel->GetComponentLocation(),
				FQuat::Identity, BikeMesh->GetCollisionObjectType(), TyreShape, Params, Responses);
		if (bRotationBlocked)
		{
			SetActorRotation(CurrentRot);
			Chassis.Reset();
			GetChassisBoxes(BikeMesh, Chassis);
		}
		const FVector VerticalMove(0,0,VerticalVelocity * DeltaTime);
		FHitResult VerticalHit;
		auto SweepVertical = [&](FVector Center, FQuat Rotation, const FCollisionShape& Shape)
		{
			FHitResult Hit;
			GetWorld()->SweepSingleByChannel(Hit, Center, Center + VerticalMove, Rotation,
				BikeMesh->GetCollisionObjectType(), Shape, Params, Responses);
			if (Hit.bBlockingHit && (!VerticalHit.bBlockingHit || Hit.Time < VerticalHit.Time)) VerticalHit = Hit;
		};
		for (const FArcadeChassisBox& Box : Chassis) SweepVertical(Box.Center, Box.Rotation, FCollisionShape::MakeBox(Box.Extent));
		for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
			if (Wheel->GetStaticMesh()) SweepVertical(Wheel->GetComponentLocation(), FQuat::Identity, TyreShape);
		if (Chassis.IsEmpty() && !FrontWheel->GetStaticMesh() && !RearWheel->GetStaticMesh())
			GetWorld()->LineTraceSingleByChannel(VerticalHit, GetActorLocation(), GetActorLocation() + VerticalMove, ECC_WorldStatic, Params);
		AddActorWorldOffset(VerticalMove * (VerticalHit.bBlockingHit ? VerticalHit.Time : 1.f), false);
		if (VerticalHit.bBlockingHit)
		{
			LastMovementHit = VerticalHit;
			if (VerticalVelocity <= 0.f && VerticalHit.ImpactNormal.Z > .7f)
			{
				bIsAirborne = false;
				LastGroundNormal = VerticalHit.ImpactNormal;
			}
			VerticalVelocity = 0.f;
		}
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
	bOutMountLeft = false;
	if (CurrentRider != nullptr || !PotentialRider || bIsAirborne || FMath::Abs(CurrentSpeed) > 50.f)
	{
		return false;
	}

	FVector LeftApproach, RightApproach;
	FRotator ApproachRotation;
	if (!GetMountApproachTransform(true, LeftApproach, ApproachRotation)
		|| !GetMountApproachTransform(false, RightApproach, ApproachRotation)) return false;
	const FVector RiderLocation = PotentialRider->GetActorLocation();
	const float DistLeft = FVector::DistSquared(RiderLocation, LeftApproach);
	const float DistRight = FVector::DistSquared(RiderLocation, RightApproach);
	bOutMountLeft = DistLeft <= DistRight;

	const FTransform UprightTransform(FRotator(0.f, GetActorRotation().Yaw, 0.f), GetActorLocation());
	const float RiderSide = UprightTransform.InverseTransformPosition(RiderLocation).Y;
	if ((bOutMountLeft && RiderSide >= 0.f) || (!bOutMountLeft && RiderSide <= 0.f)) return false;
	if (FMath::Min(DistLeft, DistRight) > FMath::Square(MountApproachRadius)) return false;

	ACarnivalPlayerCharacter* Rider = Cast<ACarnivalPlayerCharacter>(PotentialRider);
	return IsMountApproachClear(Rider,
		bOutMountLeft ? LeftApproach : RightApproach, ApproachRotation);
}

void ACarnivalMotorcycle::Mount(ACarnivalPlayerCharacter* Rider, bool bMountLeft)
{
	if (!Rider || CurrentRider != nullptr || bIsAirborne || FMath::Abs(CurrentSpeed) > 50.f
		|| !AlignRiderForMount(Rider, bMountLeft))
	{
		return;
	}

	MountingController = Rider->GetController();
	CurrentRider = Rider;
	BlockedDriveDuration = 0.f;
	CurrentRider->OnMountMotorcycle(this, bMountLeft);

	APlayerController* PC = Cast<APlayerController>(Rider->GetController());
	if (PC)
	{
		PC->Possess(this);
	}
}

bool ACarnivalMotorcycle::GetMountApproachTransform(bool bMountLeft, FVector& OutLocation, FRotator& OutRotation) const
{
	const UBoxComponent* Trigger = bMountLeft ? MountTriggerLeft : MountTriggerRight;
	if (!BikeMesh || !Trigger || !BikeMesh->DoesSocketExist(DriverSeatSocketName)) return false;

	OutRotation = FRotator(0.f, GetActorRotation().Yaw, 0.f);
	const FVector TriggerLocation = Trigger->GetComponentLocation();
	OutLocation = FVector(TriggerLocation.X, TriggerLocation.Y, 0.f);
	OutLocation.Z = BikeMesh->GetSocketLocation(DriverSeatSocketName).Z;
	return true;
}

bool ACarnivalMotorcycle::IsMountApproachClear(ACarnivalPlayerCharacter* Rider, FVector ApproachLocation, FRotator ApproachRotation) const
{
	if (!Rider || !Rider->GetCapsuleComponent() || !GetWorld()) return false;
	float Radius, HalfHeight;
	Rider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
	const FCollisionShape Capsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MotorcycleMountAlign), false, this);
	Params.AddIgnoredActor(Rider);
	if (GetWorld()->OverlapBlockingTestByProfile(ApproachLocation, ApproachRotation.Quaternion(), TEXT("Pawn"), Capsule, Params))
		return false;
	FHitResult Path;
	return !GetWorld()->SweepSingleByProfile(Path, Rider->GetActorLocation(), ApproachLocation,
		ApproachRotation.Quaternion(), TEXT("Pawn"), Capsule, Params);
}

bool ACarnivalMotorcycle::AlignRiderForMount(ACarnivalPlayerCharacter* Rider, bool bMountLeft) const
{
	FVector ApproachLocation;
	FRotator ApproachRotation;
	if (!Rider || !GetMountApproachTransform(bMountLeft, ApproachLocation, ApproachRotation)
		|| FVector::DistSquared(Rider->GetActorLocation(), ApproachLocation) > FMath::Square(MountApproachRadius)) return false;

	const FTransform UprightTransform(FRotator(0.f, GetActorRotation().Yaw, 0.f), GetActorLocation());
	const float RiderSide = UprightTransform.InverseTransformPosition(Rider->GetActorLocation()).Y;
	if ((bMountLeft && RiderSide >= 0.f) || (!bMountLeft && RiderSide <= 0.f)) return false;
	if (!IsMountApproachClear(Rider, ApproachLocation, ApproachRotation)) return false;

	Rider->SetActorLocationAndRotation(ApproachLocation, ApproachRotation, false, nullptr, ETeleportType::TeleportPhysics);
	return true;
}

bool ACarnivalMotorcycle::CanRecoverFromStuckOrOverturned() const
{
	if (bDismounting || !GetWorld() || !BikeMesh) return false;
	const bool bOverturned = GetActorUpVector().Z < .4f;
	const bool bStuck = BlockedDriveDuration >= StuckRecoveryDelay;
	return bOverturned || bStuck;
}

bool ACarnivalMotorcycle::TryRecoverFromStuckOrOverturned()
{
	if (!CanRecoverFromStuckOrOverturned()) return false;

	const FTransform CurrentTransform = GetActorTransform();
	const float HeadingYaw = GetActorRotation().Yaw;
	const FVector Heading = FRotator(0.f, HeadingYaw, 0.f).Vector();
	const FVector Right = FRotationMatrix(FRotator(0.f, HeadingYaw, 0.f)).GetUnitAxis(EAxis::Y);
	const TArray<FVector> CandidateOffsets = {
		FVector::ZeroVector,
		-Heading * 120.f,
		Right * 120.f,
		-Right * 120.f,
		Heading * 120.f,
		-Heading * 170.f + Right * 120.f,
		-Heading * 170.f - Right * 120.f
	};

	FCollisionQueryParams Params(SCENE_QUERY_STAT(MotorcycleRecovery), false, this);
	if (CurrentRider)
	{
		Params.AddIgnoredActor(CurrentRider);
	}
	const FCollisionResponseParams Responses(BikeMesh->GetCollisionResponseToChannels());
	FChassisBoxes Chassis;
	GetChassisBoxes(BikeMesh, Chassis);

	const FVector FrontWheelLocal = CurrentTransform.InverseTransformPosition(FrontWheel->GetComponentLocation());
	const FVector RearWheelLocal = CurrentTransform.InverseTransformPosition(RearWheel->GetComponentLocation());
	FVector SafeLocation = FVector::ZeroVector;
	FRotator SafeRotation = FRotator::ZeroRotator;
	FVector SafeGroundNormal = FVector::UpVector;
	bool bFoundSafePose = false;

	for (const FVector& Offset : CandidateOffsets)
	{
		const FVector Probe = GetActorLocation() + Offset;
		FHitResult Floor;
		if (!GetWorld()->LineTraceSingleByChannel(Floor, Probe + FVector(0, 0, 600),
			Probe - FVector(0, 0, 1500), ECC_WorldStatic, Params) || Floor.ImpactNormal.Z < .65f)
		{
			continue;
		}

		const float TargetPitch = FMath::RadiansToDegrees(FMath::Atan2(
			-FVector::DotProduct(Floor.ImpactNormal, Heading), FMath::Max(Floor.ImpactNormal.Z, .001f)));
		const FRotator CandidateRotation(TargetPitch, HeadingYaw, 0.f);
		const FTransform CandidateOrientation(CandidateRotation, FVector::ZeroVector, GetActorScale3D());
		const FVector FrontOffset = CandidateOrientation.TransformPosition(FrontWheelLocal);
		const FVector RearOffset = CandidateOrientation.TransformPosition(RearWheelLocal);
		const float FrontSupport = WheelRadius - FVector::DotProduct(Floor.ImpactNormal, FrontOffset);
		const float RearSupport = WheelRadius - FVector::DotProduct(Floor.ImpactNormal, RearOffset);
		FVector CandidateLocation(Probe.X, Probe.Y, Floor.ImpactPoint.Z
			+ FMath::Max(FrontSupport, RearSupport) / FMath::Max(Floor.ImpactNormal.Z, .001f));
		const FTransform CandidateTransform(CandidateRotation, CandidateLocation, GetActorScale3D());
		bool bBlocked = false;

		for (const FArcadeChassisBox& Box : Chassis)
		{
			const FVector LocalCenter = CurrentTransform.InverseTransformPosition(Box.Center);
			const FQuat LocalRotation = CurrentTransform.GetRotation().Inverse() * Box.Rotation;
			const FVector TargetCenter = CandidateTransform.TransformPosition(LocalCenter);
			const FQuat TargetBoxRotation = CandidateRotation.Quaternion() * LocalRotation;
			if (GetWorld()->OverlapBlockingTestByChannel(TargetCenter, TargetBoxRotation,
				BikeMesh->GetCollisionObjectType(), FCollisionShape::MakeBox(Box.Extent), Params, Responses))
			{
				bBlocked = true;
				break;
			}
		}
		if (bBlocked) continue;

		for (const UStaticMeshComponent* Wheel : {FrontWheel, RearWheel})
		{
			if (!Wheel->GetStaticMesh()) continue;
			const FVector WheelLocal = CurrentTransform.InverseTransformPosition(Wheel->GetComponentLocation());
			const FVector WheelCenter = CandidateTransform.TransformPosition(WheelLocal);
			if (GetWorld()->OverlapBlockingTestByChannel(WheelCenter, FQuat::Identity,
				BikeMesh->GetCollisionObjectType(), FCollisionShape::MakeSphere(FMath::Max(1.f, WheelRadius - .25f)), Params, Responses))
			{
				bBlocked = true;
				break;
			}
		}
		if (bBlocked) continue;

		SafeLocation = CandidateLocation;
		SafeRotation = CandidateRotation;
		SafeGroundNormal = Floor.ImpactNormal;
		bFoundSafePose = true;
		break;
	}

	if (!bFoundSafePose) return false;

	SetActorLocationAndRotation(SafeLocation, SafeRotation, false, nullptr, ETeleportType::TeleportPhysics);
	if (BikeMesh->IsSimulatingPhysics())
	{
		BikeMesh->SetAllPhysicsLinearVelocity(FVector::ZeroVector, false);
		BikeMesh->SetAllPhysicsAngularVelocityInDegrees(FVector::ZeroVector, false);
	}
	CurrentSpeed = VerticalVelocity = CurrentLean = WheelieAngle = SlipAngle = 0.f;
	ThrottleInput = SteeringInput = BrakeInput = BrakeReverseInput = RiderBalanceInput = 0.f;
	bHandbrake = false;
	bIsAirborne = false;
	LastGroundNormal = SafeGroundNormal;
	TravelYaw = SafeRotation.Yaw;
	bHasTravelHeading = true;
	BlockedDriveDuration = 0.f;
	LastMovementHit = FHitResult();
	return true;
}

void ACarnivalMotorcycle::ResetForStoryMissionRetry(const FTransform& StartTransform, EMotorcyclePhysicsMode StartPhysicsMode)
{
	if (CurrentRider || bDismounting)
	{
		RecoverMountedRider(true);
	}

	if (BikeMesh && BikeMesh->IsSimulatingPhysics())
	{
		BikeMesh->SetAllPhysicsLinearVelocity(FVector::ZeroVector, false);
		BikeMesh->SetAllPhysicsAngularVelocityInDegrees(FVector::ZeroVector, false);
		BikeMesh->SetSimulatePhysics(false);
	}

	SetActorTransform(StartTransform, false, nullptr, ETeleportType::TeleportPhysics);
	PhysicsMode = StartPhysicsMode;
	if (BikeMesh)
	{
		BikeMesh->SetSimulatePhysics(false);
	}
	if (CameraBoom)
	{
		CameraBoom->bInheritRoll = false;
	}
	if (FrontWheel) FrontWheel->SetRelativeRotation(FRotator::ZeroRotator);
	if (RearWheel) RearWheel->SetRelativeRotation(FRotator::ZeroRotator);

	CurrentRider = nullptr;
	bDismounting = false;
	ActiveDismountMontage = nullptr;
	LastDismountMontagePosition = 0.f;
	MountingController = nullptr;
	DismountStart = StartTransform.GetLocation();
	DismountDestination = DismountStart;
	CurrentSpeed = 0.f;
	CurrentLean = 0.f;
	VerticalVelocity = 0.f;
	WheelieAngle = 0.f;
	SlipAngle = 0.f;
	bIsAirborne = false;
	ThrottleInput = SteeringInput = BrakeInput = BrakeReverseInput = RiderBalanceInput = 0.f;
	bHandbrake = false;
	TravelYaw = StartTransform.Rotator().Yaw;
	bHasTravelHeading = true;
	WheelSpinDegrees = 0.f;
	BlockedDriveDuration = 0.f;
	LastGroundNormal = FVector::UpVector;
	LastMovementHit = FHitResult();

	SetPhysicsMode(StartPhysicsMode);
}

bool ACarnivalMotorcycle::FindDismountLocation(FVector& Location, bool& bLeft) const
{
	if (!CurrentRider) return false;
	float Radius, HalfHeight;
	CurrentRider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
	const FRotator Upright(0.f, GetActorRotation().Yaw, 0.f);
	const FVector Forward = Upright.Vector();
	const FVector Right = FRotationMatrix(Upright).GetUnitAxis(EAxis::Y);
	const float Clearance = FMath::Max(120.f, Radius + 75.f);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MotorcycleDismount), false, this);
	Params.AddIgnoredActor(CurrentRider);
	const FCollisionShape Capsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	FVector BestLocation=FVector::ZeroVector;
	float BestFloorZ=TNumericLimits<float>::Max();
	bool bFoundLocation=false;
	for (float Behind : {0.f, 70.f}) for (float Side : {-1.f, 1.f})
	{
		const FVector Candidate = GetActorLocation() + Right * (Side * Clearance) - Forward * Behind;
		FHitResult Floor;
		if (!GetWorld()->LineTraceSingleByChannel(Floor, Candidate + FVector(0,0,200), Candidate - FVector(0,0,300), ECC_WorldStatic, Params)
			|| Floor.ImpactNormal.Z < .7f || FMath::Abs(Floor.ImpactPoint.Z - GetActorLocation().Z) > 60.f) continue;
		const FVector Exit = Floor.ImpactPoint + FVector(0,0,HalfHeight + 2.f);
		if (GetWorld()->OverlapBlockingTestByProfile(Exit, FQuat::Identity, TEXT("Pawn"), Capsule, Params)) continue;
		FHitResult Path;
		if (GetWorld()->SweepSingleByProfile(Path, CurrentRider->GetActorLocation(), Exit, FQuat::Identity, TEXT("Pawn"), Capsule, Params)) continue;
		// Keep the legacy left/nearest preference on level ground. On a slope,
		// choose the lowest clear landing so the animation exits downhill instead
		// of sweeping the rider capsule into rising terrain.
		if (!bFoundLocation || Floor.ImpactPoint.Z < BestFloorZ - 1.f)
		{
			BestLocation=Exit;
			BestFloorZ=Floor.ImpactPoint.Z;
			bLeft=Side < 0.f;
			bFoundLocation=true;
		}
	}
	if (bFoundLocation) Location=BestLocation;
	return bFoundLocation;
}

void ACarnivalMotorcycle::Dismount()
{
	if (TryRecoverFromStuckOrOverturned()) return;
	if (!CurrentRider || bDismounting || bIsAirborne || FMath::Abs(CurrentSpeed)>50.f)
	{
		return;
	}
	FVector ExitLocation;
	bool bExitLeft;
	if (!FindDismountLocation(ExitLocation, bExitLeft)) return;
	UAnimMontage* Montage=bExitLeft ? CurrentRider->DismountLeftMontage : CurrentRider->DismountRightMontage;
	if (Montage && CurrentRider->PlayAnimMontage(Montage)>0.f)
	{
		DismountStart=CurrentRider->GetActorLocation();
		DismountDestination=ExitLocation;
		bDismountLeft=bExitLeft;
		ActiveDismountMontage=Montage;
		LastDismountMontagePosition=0.f;
		bDismounting=true;
		CurrentSpeed=0.f;
		ThrottleInput=SteeringInput=BrakeInput=BrakeReverseInput=RiderBalanceInput=0.f;
		bHandbrake=false;
		return;
	}
	DismountDestination=ExitLocation; bDismountLeft=bExitLeft;
	CompleteDismount();
}

void ACarnivalMotorcycle::UpdateDismount()
{
	if (!IsValid(CurrentRider)) { CurrentRider=nullptr; bDismounting=false; ActiveDismountMontage=nullptr; LastDismountMontagePosition=0.f; return; }
	UAnimInstance* Anim=CurrentRider->GetMesh()->GetAnimInstance();
	const bool bHasMontage=Anim && ActiveDismountMontage;
	const float MontageLength=ActiveDismountMontage ? ActiveDismountMontage->GetPlayLength() : 0.f;
	const bool bPlaying=bHasMontage && Anim->Montage_IsPlaying(ActiveDismountMontage);
	const float MontagePosition=bHasMontage ? Anim->Montage_GetPosition(ActiveDismountMontage) : 0.f;
	if (bPlaying) LastDismountMontagePosition=FMath::Max(LastDismountMontagePosition,MontagePosition);
	// In live PIE the animation instance can finish ticking before the bike. On
	// that final frame Montage_IsPlaying is already false, so retain the last
	// near-end position and let the checked exit complete instead of cancelling.
	const bool bMontageFinished=!bPlaying && MontageLength>0.f
		&& LastDismountMontagePosition>=MontageLength-.10f;
	const bool bAnimationAvailable=bPlaying || bMontageFinished;
	float Radius,HalfHeight;
	CurrentRider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius,HalfHeight);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MotorcycleExitStage),false,this);
	Params.AddIgnoredActor(CurrentRider);
	const FCollisionShape Capsule=FCollisionShape::MakeCapsule(Radius,HalfHeight);
	FHitResult Floor;
	const bool bFloor=GetWorld()->LineTraceSingleByChannel(Floor,DismountDestination,DismountDestination-FVector(0,0,HalfHeight+20),ECC_WorldStatic,Params)
		&& Floor.ImpactNormal.Z>.7f && FMath::Abs(Floor.ImpactPoint.Z-(DismountDestination.Z-HalfHeight-2.f))<5.f;
	FVector ExitOffset=FVector::ZeroVector;
	float ExitWarp=0.f;
	if (bAnimationAvailable && !ActiveDismountMontage->SlotAnimTracks.IsEmpty())
	{
		const float Position=bPlaying ? MontagePosition : LastDismountMontagePosition;
		const FAnimSegment* Segment=ActiveDismountMontage->SlotAnimTracks[0].AnimTrack.GetSegmentAtTime(Position);
		if (Segment && Segment->GetAnimReference())
		{
			const UAnimSequenceBase* Clip=Segment->GetAnimReference();
			const float Time=Segment->ConvertTrackPosToAnimPos(Position);
			auto Curve=[&](FName Name,float At) { return Clip->EvaluateCurveData(Name,FAnimExtractContext(At,false)); };
			auto Offset=[&](float At) { return FRotator(0,GetActorRotation().Yaw,0).RotateVector(
				FVector(Curve(TEXT("BikeExitX"),At),Curve(TEXT("BikeExitY"),At),Curve(TEXT("BikeExitZ"),At))); };
			ExitWarp=FMath::Clamp(Curve(TEXT("BikeExitWarp"),Time),0.f,1.f);
			// Follow authored movement while the foot supports the rider on the
			// peg. Add destination correction only after the support foot lifts.
			ExitOffset=Offset(Time)+(DismountDestination-DismountStart-Offset(Clip->GetPlayLength()))*ExitWarp;
		}
	}
	FVector Next=DismountStart+ExitOffset;
	if (bPlaying && bFloor)
	{
		// Follow the local floor profile during the root path as well. The late
		// exit warp already includes the full destination height, so subtract its
		// portion here to avoid lifting twice at the end of a sloped dismount.
		FHitResult StartGround;
		FHitResult CurrentGround;
		const bool bStartGround=GetWorld()->LineTraceSingleByChannel(StartGround,DismountStart+FVector(0,0,250),DismountStart-FVector(0,0,250),ECC_WorldStatic,Params);
		const bool bCurrentGround=GetWorld()->LineTraceSingleByChannel(CurrentGround,Next+FVector(0,0,250),Next-FVector(0,0,250),ECC_WorldStatic,Params);
		if (bStartGround && bCurrentGround)
		{
			const float CurrentGroundDelta=CurrentGround.ImpactPoint.Z-StartGround.ImpactPoint.Z;
			const float DestinationGroundDelta=Floor.ImpactPoint.Z-StartGround.ImpactPoint.Z;
			ExitOffset.Z+=CurrentGroundDelta-DestinationGroundDelta*ExitWarp;
			Next=DismountStart+ExitOffset;
		}
	}
	FHitResult Path;
	const bool bDestinationBlocked=GetWorld()->OverlapBlockingTestByProfile(DismountDestination,FQuat::Identity,TEXT("Pawn"),Capsule,Params);
	const bool bPathBlocked=GetWorld()->SweepSingleByProfile(Path,CurrentRider->GetActorLocation(),Next,FQuat::Identity,TEXT("Pawn"),Capsule,Params);
	const bool bBlocked=bDestinationBlocked || bPathBlocked;
	if (!bAnimationAvailable || !bFloor || bBlocked)
	{
		// An interrupted or newly blocked exit restores riding ownership.
		if (Anim) Anim->Montage_Stop(.1f,ActiveDismountMontage);
		CurrentRider->AttachToComponent(BikeMesh,FAttachmentTransformRules::SnapToTargetNotIncludingScale,DriverSeatSocketName);
		bDismounting=false; ActiveDismountMontage=nullptr; LastDismountMontagePosition=0.f;
		return;
	}
	CurrentRider->SetActorLocation(Next);
	if (bMontageFinished || (bPlaying && MontagePosition>=MontageLength-.02f))
	{
		CurrentRider->SetActorLocation(DismountDestination);
		Anim->Montage_Stop(.15f,ActiveDismountMontage);
		CompleteDismount();
	}
}

void ACarnivalMotorcycle::CompleteDismount()
{
	if (!CurrentRider) { bDismounting=false; LastDismountMontagePosition=0.f; return; }

	ACarnivalPlayerCharacter* RiderToRestore = CurrentRider;
	// Place the still non-colliding character outside the vehicle before its
	// capsule/walking mode are restored. Failed exits leave ownership intact.
	RiderToRestore->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	RiderToRestore->SetActorLocationAndRotation(DismountDestination, FRotator(0.f, GetActorRotation().Yaw, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
	CurrentRider = nullptr;
	bDismounting=false; ActiveDismountMontage=nullptr; LastDismountMontagePosition=0.f;
	BlockedDriveDuration = 0.f;
	ThrottleInput = SteeringInput = BrakeInput = BrakeReverseInput = RiderBalanceInput = 0.f;
	bHandbrake = false;

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (PC && RiderToRestore)
	{
		PC->Possess(RiderToRestore);
	}
	MountingController = nullptr;

	RiderToRestore->OnDismountMotorcycle(this, bDismountLeft);
}

void ACarnivalMotorcycle::HandleLostPossessionRecovery()
{
	if (!IsValid(CurrentRider))
	{
		CurrentRider = nullptr;
		MountingController = nullptr;
		BlockedDriveDuration = 0.f;
		return;
	}

	AController* FormerController = MountingController;
	if (FormerController)
	{
		APawn* NewPawn = FormerController->GetPawn();
		// Possession changes can transiently call UnPossessed while this bike is
		// immediately possessed again. The deferred check runs after the handoff;
		// if the controller still owns this bike, the rider remains mounted.
		if (NewPawn == this) return;
		// A controller switching to another pawn is an intentional handoff.
		if (NewPawn && NewPawn != CurrentRider) return;
	}
	RecoverMountedRider(FormerController && FormerController->GetPawn() == nullptr);
}

void ACarnivalMotorcycle::RecoverMountedRider(bool bRestorePossession)
{
	ACarnivalPlayerCharacter* RiderToRestore = IsValid(CurrentRider) ? CurrentRider : nullptr;
	AController* FormerController = MountingController ? MountingController : GetController();
	if (!RiderToRestore)
	{
		CurrentRider = nullptr;
		bDismounting = false;
		ActiveDismountMontage = nullptr;
		LastDismountMontagePosition = 0.f;
		MountingController = nullptr;
		BlockedDriveDuration = 0.f;
		return;
	}

	float Radius, HalfHeight;
	RiderToRestore->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
	FVector RecoveryLocation;
	bool bRecoveryLeft = true;
	bool bHasGround = FindDismountLocation(RecoveryLocation, bRecoveryLeft);

	const FRotator Upright(0.f, GetActorRotation().Yaw, 0.f);
	const FVector Forward = Upright.Vector();
	const FVector Right = FRotationMatrix(Upright).GetUnitAxis(EAxis::Y);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MotorcycleEmergencyRecovery), false, this);
	Params.AddIgnoredActor(RiderToRestore);
	const FCollisionShape Capsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	auto IsClear = [&](const FVector& Location)
	{
		return !GetWorld()->OverlapBlockingTestByProfile(Location, FQuat::Identity, TEXT("Pawn"), Capsule, Params);
	};
	auto HasClearPath = [&](const FVector& Location)
	{
		FHitResult Path;
		return !GetWorld()->SweepSingleByProfile(Path, RiderToRestore->GetActorLocation(), Location,
			FQuat::Identity, TEXT("Pawn"), Capsule, Params);
	};

	// Emergency recovery may skip the animated path, but it still prefers a
	// supported, capsule-clear landing beside or behind the bike.
	if (!bHasGround)
	{
		for (float SideDistance : {FMath::Max(120.f, Radius + 75.f), FMath::Max(180.f, Radius + 135.f), FMath::Max(260.f, Radius + 215.f)})
		{
			for (float Behind : {0.f, 90.f})
			{
				for (float Side : {-1.f, 1.f})
				{
					const FVector Probe = GetActorLocation() + Right * (Side * SideDistance) - Forward * Behind;
					FHitResult Floor;
					if (!GetWorld()->LineTraceSingleByChannel(Floor, Probe + FVector(0,0,300),
						Probe - FVector(0,0,1200), ECC_WorldStatic, Params) || Floor.ImpactNormal.Z < .7f) continue;
					const FVector Candidate = Floor.ImpactPoint + FVector(0,0,HalfHeight + 2.f);
					if (!IsClear(Candidate) || !HasClearPath(Candidate)) continue;
					RecoveryLocation = Candidate;
					bRecoveryLeft = Side < 0.f;
					bHasGround = true;
					break;
				}
				if (bHasGround) break;
			}
			if (bHasGround) break;
		}
	}

	// If the bike is airborne or no walkable floor remains, eject clear of its
	// body and let character movement fall until it finds ground.
	if (!bHasGround)
	{
		bool bFoundAirClearance = false;
		for (float SideDistance : {FMath::Max(120.f, Radius + 75.f), FMath::Max(200.f, Radius + 155.f)})
		{
			for (float Side : {-1.f, 1.f})
			{
				const FVector Candidate = GetActorLocation() + Right * (Side * SideDistance)
					+ FVector(0,0,HalfHeight + 100.f);
				if (!IsClear(Candidate) || !HasClearPath(Candidate)) continue;
				RecoveryLocation = Candidate;
				bRecoveryLeft = Side < 0.f;
				bFoundAirClearance = true;
				break;
			}
			if (bFoundAirClearance) break;
		}
		if (!bFoundAirClearance)
		{
			RecoveryLocation = RiderToRestore->GetActorLocation() + FVector(0,0,HalfHeight + 25.f);
		}
	}

	CurrentRider = nullptr;
	bDismounting = false;
	ActiveDismountMontage = nullptr;
	LastDismountMontagePosition = 0.f;
	BlockedDriveDuration = 0.f;
	CurrentSpeed = 0.f;
	VerticalVelocity = 0.f;
	ThrottleInput = SteeringInput = BrakeInput = BrakeReverseInput = RiderBalanceInput = 0.f;
	bHandbrake = false;

	if (UAnimInstance* Anim = RiderToRestore->GetMesh()->GetAnimInstance()) Anim->Montage_Stop(.1f);
	RiderToRestore->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	RiderToRestore->SetActorLocationAndRotation(RecoveryLocation, FRotator(0.f, GetActorRotation().Yaw, 0.f),
		false, nullptr, ETeleportType::TeleportPhysics);
	RiderToRestore->OnDismountMotorcycle(this, bRecoveryLeft);
	if (!bHasGround) RiderToRestore->GetCharacterMovement()->SetMovementMode(MOVE_Falling);

	if (bRestorePossession && FormerController &&
		(!FormerController->GetPawn() || FormerController->GetPawn() == this))
	{
		FormerController->Possess(RiderToRestore);
	}
	MountingController = nullptr;
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
	ThrottleInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalMotorcycle::InputSteering(float Value)
{
	SteeringInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalMotorcycle::InputBrake(float Value)
{
	BrakeInput = FMath::Clamp(Value, 0.f, 1.f);
}

void ACarnivalMotorcycle::InputHandbrake(bool bPressed)
{
	bHandbrake = bPressed;
}

void ACarnivalMotorcycle::InputBrakeReverse(float Value)
{
	BrakeReverseInput = FMath::Clamp(Value, 0.f, 1.f);
}

void ACarnivalMotorcycle::InputRiderBalance(float Value)
{
	RiderBalanceInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalMotorcycle::UnPossessed()
{
	ThrottleInput = 0.f;
	SteeringInput = 0.f;
	BrakeInput = 0.f;
	BrakeReverseInput = 0.f;
	bHandbrake = false;
	RiderBalanceInput = 0.f;
	Super::UnPossessed();
	if (CurrentRider && GetWorld())
	{
		GetWorld()->GetTimerManager().SetTimerForNextTick(
			FTimerDelegate::CreateUObject(this, &ACarnivalMotorcycle::HandleLostPossessionRecovery));
	}
}

void ACarnivalMotorcycle::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
}
