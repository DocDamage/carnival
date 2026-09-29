// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalBoat.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalVehicleExit.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "TimerManager.h"

ACarnivalBoat::ACarnivalBoat()
{
	PrimaryActorTick.bCanEverTick = true;

	CollisionBox = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionBox"));
	CollisionBox->SetBoxExtent(FVector(300.0f, 120.0f, 80.0f));
	CollisionBox->SetCollisionProfileName(TEXT("Vehicle"));
	CollisionBox->SetSimulatePhysics(false);
	RootComponent = CollisionBox;

	BoatMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BoatMesh"));
	BoatMesh->SetupAttachment(RootComponent);
	BoatMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	PropellerMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PropellerMesh"));
	PropellerMesh->SetupAttachment(BoatMesh);
	PropellerMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	MountTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("MountTrigger"));
	MountTrigger->SetupAttachment(RootComponent);
	MountTrigger->SetBoxExtent(FVector(350.0f, 180.0f, 100.0f));
	MountTrigger->SetCollisionProfileName(TEXT("Trigger"));

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 900.0f;
	CameraBoom->SetRelativeRotation(FRotator(-15.0f, 0.0f, 0.0f));
	CameraBoom->SocketOffset = FVector(0.0f, 0.0f, 200.0f);
	CameraBoom->bUsePawnControlRotation = false;
	CameraBoom->bInheritPitch = false;
	CameraBoom->bInheritRoll = false;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 6.0f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
}

void ACarnivalBoat::BeginPlay()
{
	Super::BeginPlay();
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bInheritPitch = true;
	CameraBoom->bInheritYaw = true;

	TargetWaterZ = WaterPlaneZ;

	// Trace downward to find initial water plane
	if (bAutoDetectWater)
	{
		FHitResult Hit;
		FVector Start = GetActorLocation() + FVector(0.0f, 0.0f, 500.0f);
		FVector End = GetActorLocation() - FVector(0.0f, 0.0f, 2000.0f);
		FCollisionQueryParams Params;
		Params.AddIgnoredActor(this);

		if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_WorldStatic, Params))
		{
			// Check if actor has water in name or material
			FString ActorName = Hit.GetActor() ? Hit.GetActor()->GetName().ToLower() : TEXT("");
			if (ActorName.Contains(TEXT("water")) || ActorName.Contains(TEXT("ocean")))
			{
				TargetWaterZ = Hit.ImpactPoint.Z;
			}
			else
			{
				TargetWaterZ = GetActorLocation().Z;
			}
		}
		else
		{
			TargetWaterZ = GetActorLocation().Z;
		}
	}
}

void ACarnivalBoat::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	UpdateWaterPhysics(DeltaTime);
}

void ACarnivalBoat::UpdateWaterPhysics(float DeltaTime)
{
	// 1. Throttle / Acceleration
	float TargetSpeed = 0.0f;
	if (ThrottleInput > 0.0f && BrakeInput <= 0.f)
	{
		TargetSpeed = MaxForwardSpeed * ThrottleInput;
	}
	else if (ThrottleInput < 0.0f && BrakeInput <= 0.f)
	{
		TargetSpeed = MaxReverseSpeed * ThrottleInput;
	}

	float AccelRate = (FMath::Abs(TargetSpeed) > FMath::Abs(CurrentSpeed)) ? Acceleration : BrakingDeceleration;
	CurrentSpeed = FMath::FInterpTo(CurrentSpeed, TargetSpeed, DeltaTime, AccelRate / 500.0f);

	if (BrakeInput > 0.0f)
	{
		CurrentSpeed = FMath::FInterpTo(CurrentSpeed, 0.0f, DeltaTime, (BrakingDeceleration * BrakeInput) / 200.0f);
	}

	// 2. Rudder Steering (Yaw authority scales with speed)
	float SpeedRatio = FMath::Clamp(FMath::Abs(CurrentSpeed) / FMath::Max(1.f, MaxForwardSpeed * 0.5f), 0.0f, 1.0f);
	float TurnDirection = (CurrentSpeed >= 0.0f) ? 1.0f : -1.0f;
	float YawDelta = SteeringInput * TurnRate * SpeedRatio * TurnDirection * DeltaTime;

	// 3. Dynamic Banking & Pitch
	float TargetBank = -SteeringInput * MaxBankAngle * FMath::Clamp(CurrentSpeed / 1200.0f, -1.0f, 1.0f);
	CurrentBank = FMath::FInterpTo(CurrentBank, TargetBank, DeltaTime, 4.0f);

	// Bow rise under forward thrust
	float TargetPitch = FMath::Clamp(CurrentSpeed / FMath::Max(1.f, MaxForwardSpeed), 0.0f, 1.0f) * 6.0f;
	CurrentPitch = FMath::FInterpTo(CurrentPitch, TargetPitch, DeltaTime, 3.0f);

	// 4. Wave Bobbing Simulation
	WaveTime += DeltaTime * WaveBobFrequency;
	float WaveOffset = FMath::Sin(WaveTime) * WaveBobAmplitude;
	float WavePitch = FMath::Cos(WaveTime * 0.8f) * (WaveBobAmplitude * 0.15f);
	float WaveRoll = FMath::Sin(WaveTime * 1.2f) * (WaveBobAmplitude * 0.12f);

	// 5. Position & Rotation Integration
	FVector ForwardMove = GetActorForwardVector() * CurrentSpeed * DeltaTime;
	FVector NewLocation = GetActorLocation() + ForwardMove;
	NewLocation.Z = FMath::FInterpTo(GetActorLocation().Z, TargetWaterZ + WaveOffset, DeltaTime, 6.0f);

	FRotator NewRotation = FRotator(
		CurrentPitch + WavePitch,
		GetActorRotation().Yaw + YawDelta,
		CurrentBank + WaveRoll
	);

	if (bUseNavigableWaterBounds)
	{
		// Sample the whole move, including rotation, so a long frame cannot jump
		// a narrow shoal. The normal hull sweep still handles docks and obstacles.
		const FVector OldLocation = GetActorLocation();
		const FQuat OldRotation = GetActorQuat();
		const FQuat TargetRotation = NewRotation.Quaternion();
		const FVector Extent = CollisionBox->GetScaledBoxExtent();
		const float CornerTravel = FVector::Distance(OldLocation, NewLocation)
			+ OldRotation.AngularDistance(TargetRotation) * Extent.Size();
		const int32 Steps = FMath::Max(1, FMath::CeilToInt(CornerTravel / 40.f));
		bool bNavigable = Steps <= 128;
		for (int32 Step = 1; bNavigable && Step <= Steps; ++Step)
		{
			const float Alpha = static_cast<float>(Step) / Steps;
			bNavigable = IsWaterTransformNavigable(FMath::Lerp(OldLocation, NewLocation, Alpha),
				FQuat::Slerp(OldRotation, TargetRotation, Alpha).Rotator());
		}
		if (!bNavigable)
		{
			CurrentSpeed = 0.f;
			return;
		}
	}

	FHitResult SweepHit;
	SetActorLocationAndRotation(NewLocation, NewRotation, true, &SweepHit);
	if (SweepHit.bBlockingHit) CurrentSpeed = 0.f;

	// 6. Propeller Spin
	if (PropellerMesh)
	{
		PropellerMesh->AddLocalRotation(FRotator(0.0f, 0.0f, CurrentSpeed * DeltaTime * 8.0f));
	}
}

bool ACarnivalBoat::IsWaterTransformNavigable(FVector Location, FRotator Rotation) const
{
	if (!bUseNavigableWaterBounds) return true;
	if (!GetWorld() || !CollisionBox || Location.ContainsNaN() || Rotation.ContainsNaN()
		|| NavigableWaterMin.ContainsNaN() || NavigableWaterMax.ContainsNaN()
		|| NavigableWaterMin.X >= NavigableWaterMax.X || NavigableWaterMin.Y >= NavigableWaterMax.Y)
	{
		return false;
	}
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalBoatKeel), false, this);
	if (CurrentRider) Params.AddIgnoredActor(CurrentRider);
	const FVector Extent = CollisionBox->GetScaledBoxExtent();
	const FQuat Quaternion = Rotation.Quaternion();
	const float Clearance = FMath::Max(0.f, MinimumKeelClearance);
	// All eight projected corners must remain inside the surveyed rectangle.
	// Ground is checked below the center and corners, including bank/pitch.
	for (int32 Point = -1; Point < 8; ++Point)
	{
		const FVector Local = Point < 0 ? FVector::ZeroVector : FVector(
			(Point & 1) ? Extent.X : -Extent.X,
			(Point & 2) ? Extent.Y : -Extent.Y,
			(Point & 4) ? Extent.Z : -Extent.Z);
		const FVector Corner = Location + Quaternion.RotateVector(Local);
		if (Corner.X < NavigableWaterMin.X || Corner.X > NavigableWaterMax.X
			|| Corner.Y < NavigableWaterMin.Y || Corner.Y > NavigableWaterMax.Y) return false;
		FHitResult Ground;
		const FVector Start(Corner.X, Corner.Y, Location.Z + Extent.Size() + Clearance);
		const FVector End(Corner.X, Corner.Y, FMath::Min(Location.Z - Extent.Z, Corner.Z) - Clearance);
		// Project WaterBodyCollision ignores Visibility; its WorldStatic object
		// channel would incorrectly report the water surface itself as a shoal.
		if (GetWorld()->LineTraceSingleByChannel(Ground, Start, End, ECC_Visibility, Params)) return false;
	}
	return true;
}

void ACarnivalBoat::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	if (Cast<ACarnivalPlayerController>(GetController())) return;

	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ACarnivalBoat::InputThrottle);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACarnivalBoat::InputSteering);
	PlayerInputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &ACarnivalBoat::Dismount);
}

void ACarnivalBoat::InputThrottle(float Value)
{
	ThrottleInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalBoat::InputSteering(float Value)
{
	SteeringInput = FMath::Clamp(Value, -1.f, 1.f);
}

void ACarnivalBoat::InputBrake(float Value)
{
	BrakeInput = FMath::Clamp(Value, 0.f, 1.f);
}

bool ACarnivalBoat::CanMount(AActor* PotentialRider) const
{
	const ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(PotentialRider);
	if (CurrentRider != nullptr || !IsValid(Player) || !Player->GetController()
		|| Player->MountedMotorcycle || Player->MountedBoat || Player->MountedHovercraft
		|| Player->IsUsingRide() || FMath::Abs(CurrentSpeed) > 50.f)
	{
		return false;
	}

	return MountTrigger->IsOverlappingActor(PotentialRider)
		&& CarnivalVehicleExit::CanReachSeat(this, Player, DriverRelativeOffset);
}

void ACarnivalBoat::Mount(ACarnivalPlayerCharacter* Rider)
{
	if (!CanMount(Rider))
	{
		return;
	}

	BoardingTransform = Rider->GetActorTransform();
	BoardingController = Rider->GetController();
	ClearControlInputs();
	CurrentRider = Rider;

	// Notify player character
	Rider->OnMountBoat(this);

	// Possess boat
	AController* RiderController = Rider->GetController();
	if (RiderController)
	{
		RiderController->Possess(this);
	}
}

void ACarnivalBoat::Dismount()
{
	if (FMath::Abs(CurrentSpeed) <= 50.f) RestoreRider(false);
}

void ACarnivalBoat::ClearControlInputs()
{
	ThrottleInput = SteeringInput = BrakeInput = 0.f;
}

void ACarnivalBoat::UnPossessed()
{
	ClearControlInputs();
	Super::UnPossessed();
	if (CurrentRider && GetWorld()) GetWorld()->GetTimerManager().SetTimerForNextTick(
		FTimerDelegate::CreateUObject(this, &ACarnivalBoat::RecoverLostPossession));
}

void ACarnivalBoat::RecoverLostPossession()
{
	if (!GetController() && CurrentRider) RestoreRider(true);
}

void ACarnivalBoat::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (EndPlayReason == EEndPlayReason::Destroyed) RestoreRider(true);
	Super::EndPlay(EndPlayReason);
}

void ACarnivalBoat::RestoreRider(bool bEmergency)
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
	CurrentSpeed = 0.f;
	Rider->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	Rider->SetActorLocationAndRotation(Exit, FRotator(0, GetActorRotation().Yaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
	Rider->OnDismountBoat();
	Rider->GetCharacterMovement()->StopMovementImmediately();
	if (FormerController && (!FormerController->GetPawn() || FormerController->GetPawn() == this)) FormerController->Possess(Rider);
	BoardingController.Reset();
}
