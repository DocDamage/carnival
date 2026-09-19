// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalBoat.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"

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
	if (ThrottleInput > 0.0f)
	{
		TargetSpeed = MaxForwardSpeed * ThrottleInput;
	}
	else if (ThrottleInput < 0.0f)
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
	float SpeedRatio = FMath::Clamp(FMath::Abs(CurrentSpeed) / (MaxForwardSpeed * 0.5f), 0.2f, 1.0f);
	float TurnDirection = (CurrentSpeed >= 0.0f) ? 1.0f : -1.0f;
	float YawDelta = SteeringInput * TurnRate * SpeedRatio * TurnDirection * DeltaTime;

	// 3. Dynamic Banking & Pitch
	float TargetBank = -SteeringInput * MaxBankAngle * FMath::Clamp(CurrentSpeed / 1200.0f, -1.0f, 1.0f);
	CurrentBank = FMath::FInterpTo(CurrentBank, TargetBank, DeltaTime, 4.0f);

	// Bow rise under forward thrust
	float TargetPitch = FMath::Clamp(CurrentSpeed / MaxForwardSpeed, 0.0f, 1.0f) * 6.0f;
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

	FHitResult SweepHit;
	SetActorLocationAndRotation(NewLocation, NewRotation, true, &SweepHit);

	// 6. Propeller Spin
	if (PropellerMesh)
	{
		PropellerMesh->AddLocalRotation(FRotator(0.0f, 0.0f, CurrentSpeed * DeltaTime * 8.0f));
	}
}

void ACarnivalBoat::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ACarnivalBoat::InputThrottle);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACarnivalBoat::InputSteering);
	PlayerInputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &ACarnivalBoat::Dismount);
}

void ACarnivalBoat::InputThrottle(float Value)
{
	ThrottleInput = Value;
}

void ACarnivalBoat::InputSteering(float Value)
{
	SteeringInput = Value;
}

void ACarnivalBoat::InputBrake(float Value)
{
	BrakeInput = Value;
}

bool ACarnivalBoat::CanMount(AActor* PotentialRider) const
{
	if (CurrentRider != nullptr || PotentialRider == nullptr)
	{
		return false;
	}

	return MountTrigger->IsOverlappingActor(PotentialRider);
}

void ACarnivalBoat::Mount(ACarnivalPlayerCharacter* Rider)
{
	if (!Rider || CurrentRider)
	{
		return;
	}

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
	if (!CurrentRider)
	{
		return;
	}

	ACarnivalPlayerCharacter* Rider = CurrentRider;
	CurrentRider = nullptr;

	// Unpossess boat and return control to rider
	AController* BoatController = GetController();
	if (BoatController)
	{
		BoatController->Possess(Rider);
	}

	// Notify character to dismount
	Rider->OnDismountBoat();
}

