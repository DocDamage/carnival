#include "CarnivalBumperCar.h"
#include "CarnivalBumperArenaComponent.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalRideOperationComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "CarnivalVehicleExit.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/Controller.h"
#include "Camera/CameraComponent.h"
#include "TimerManager.h"

ACarnivalBumperCar::ACarnivalBumperCar()
{
    PrimaryActorTick.bCanEverTick = true;
    Hull = CreateDefaultSubobject<UBoxComponent>(TEXT("Hull"));
    SetRootComponent(Hull);
    Hull->SetBoxExtent(FVector(95, 65, 35));
    Hull->SetCollisionProfileName(TEXT("Vehicle"));
    CarMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CarMesh"));
    CarMesh->SetupAttachment(Hull);
    CarMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DriverSeat = CreateDefaultSubobject<UCarnivalRideSeatComponent>(TEXT("DriverSeat"));
    DriverSeat->SetupAttachment(Hull);
    DriverSeat->SetAbsolute(false, false, true);
    DriverSeat->SetRelativeLocation(FVector(0, 0, 35));
    DriverSeat->SeatId = TEXT("Driver");
    DriverSeat->PassengerOffset = FTransform(FVector(16.69f, -.28f, 51.4f));
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(Hull);
    CameraBoom->SetRelativeLocation(FVector(0, 0, 100));
    CameraBoom->TargetArmLength = 400.f;
    CameraBoom->bUsePawnControlRotation = true;
    CameraBoom->bInheritRoll = false;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom);
}

bool ACarnivalBumperCar::CanBoard(ACarnivalPlayerCharacter* Rider) const
{
    const auto* Operation = Arena ? Arena->GetOperation() : nullptr;
    if (!IsValid(Rider) || !Rider->GetController() || CurrentRider || !Operation || !Operation->IsReady()
        || Operation->State != ECarnivalOperationState::Loading || !Operation->IsInInteractionRange(Rider)
        || Operation->PlayerOperator == Rider || !IsStopped()
        || Rider->IsUsingRide() || Rider->IsParkourTraversing() || Rider->MountedMotorcycle || Rider->MountedBoat || Rider->MountedHovercraft)
        return false;
    const FVector SeatOffset = GetActorTransform().InverseTransformPosition(DriverSeat->GetPassengerWorldTransform().GetLocation());
    return CarnivalVehicleExit::CanReachSeat(this, Rider, SeatOffset);
}

bool ACarnivalBumperCar::Board(ACarnivalPlayerCharacter* Rider)
{
    if (!CanBoard(Rider)) return false;
    BoardingTransform = Rider->GetActorTransform();
    BoardingController = Rider->GetController();
    if (!Rider->RidePassenger->BoardRide(this, DriverSeat)) return false;
    CurrentRider = Rider;
    ClearControlInputs();
    BoardingController->Possess(this);
    return true;
}

void ACarnivalBumperCar::InputThrottle(float Value) { Throttle = FMath::Clamp(Value, -1.f, 1.f); }
void ACarnivalBumperCar::InputSteering(float Value) { Steering = FMath::Clamp(Value, -1.f, 1.f); }
void ACarnivalBumperCar::InputBrake(float Value) { Brake = FMath::Clamp(Value, 0.f, 1.f); }
void ACarnivalBumperCar::ClearControlInputs() { Throttle = Steering = Brake = 0.f; }
bool ACarnivalBumperCar::IsStopped() const { return FMath::Abs(CurrentSpeed) < 10.f && BumpVelocity.Size2D() < 10.f; }

void ACarnivalBumperCar::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (DeltaSeconds <= 0.f) return;
    const bool bDriving = Arena && Arena->IsDrivingEnabled();
    const float Target = bDriving && Brake < .01f && CurrentRider && GetController() ? Throttle * MaxSpeed : 0.f;
    CurrentSpeed = FMath::FInterpConstantTo(CurrentSpeed, Target, DeltaSeconds,
        !bDriving || Brake > .01f ? Braking : Acceleration);
    if (bDriving && FMath::Abs(CurrentSpeed) > 1.f)
    {
        const FRotator Rotation = GetActorRotation() + FRotator(0, Steering * TurnRate * DeltaSeconds * FMath::Sign(CurrentSpeed), 0);
        FCollisionQueryParams RotationParams(SCENE_QUERY_STAT(BumperTurn), false, this);
        if (CurrentRider) RotationParams.AddIgnoredActor(CurrentRider);
        if (!GetWorld()->OverlapBlockingTestByProfile(GetActorLocation(), Rotation.Quaternion(), TEXT("Vehicle"),
            FCollisionShape::MakeBox(Hull->GetScaledBoxExtent()), RotationParams)) SetActorRotation(Rotation);
    }
    BumpVelocity = FMath::VInterpTo(BumpVelocity, FVector::ZeroVector, DeltaSeconds, bDriving ? 2.f : 8.f);
    const FVector Velocity = GetActorForwardVector() * CurrentSpeed + BumpVelocity;
    const FVector Delta = Velocity * DeltaSeconds;
    const FVector Candidate = GetActorLocation() + Delta;
    const float Radius = Hull->GetScaledBoxExtent().Size2D();
    FHitResult Floor;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BumperFloor), false, this);
    if (CurrentRider) Params.AddIgnoredActor(CurrentRider);
    const bool bSupported = GetWorld()->LineTraceSingleByChannel(Floor, Candidate + FVector(0, 0, 10),
        Candidate - FVector(0, 0, Hull->GetScaledBoxExtent().Z + 35), ECC_Visibility, Params) && Floor.ImpactNormal.Z > .7f;
    if (!Arena || !Arena->ContainsCarLocation(Candidate, Radius) || !bSupported)
    {
        CurrentSpeed = 0.f;
        BumpVelocity = -Velocity * .3f;
        return;
    }
    FHitResult Hit;
    SetActorLocation(Candidate, true, &Hit);
    if (Hit.bBlockingHit)
    {
        CurrentSpeed = 0.f;
        BumpVelocity = Velocity.MirrorByVector(Hit.Normal) * .45f;
        BumpVelocity.Z = 0.f;
        if (auto* Other = Cast<ACarnivalBumperCar>(Hit.GetActor()))
            Other->BumpVelocity += Velocity * .35f;
    }
}

bool ACarnivalBumperCar::FindExit(FVector& Location, bool bEmergency) const
{
    if (!CurrentRider) return false;
    if (CarnivalVehicleExit::FindGroundExit(const_cast<ACarnivalBumperCar*>(this), CurrentRider, Hull->GetScaledBoxExtent(), Location)) return true;
    if (!bEmergency) return false;
    float Radius, HalfHeight;
    CurrentRider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BumperEmergencyExit), false, this);
    Params.AddIgnoredActor(CurrentRider);
    for (int32 Index = 0; Index < 25; ++Index)
    {
        const FVector Offset = Index == 0 ? FVector::ZeroVector : FRotator(0, Index * 45.f, 0).Vector() * (120.f * (1 + (Index-1)/8));
        const FVector Probe = BoardingTransform.GetLocation() + Offset;
        FHitResult Floor;
        if (GetWorld()->LineTraceSingleByChannel(Floor, Probe + FVector(0, 0, 150), Probe - FVector(0, 0, 300), ECC_Visibility, Params)
            && Floor.ImpactNormal.Z > .7f)
        {
            const FVector Candidate = Floor.ImpactPoint + FVector(0, 0, HalfHeight + 2);
            if (!GetWorld()->OverlapBlockingTestByProfile(Candidate, FQuat::Identity, TEXT("Pawn"), FCollisionShape::MakeCapsule(Radius, HalfHeight), Params))
            { Location = Candidate; return true; }
        }
    }
    return false;
}

void ACarnivalBumperCar::RestoreRider(const FVector& ExitLocation)
{
    if (!CurrentRider || bRestoring) return;
    bRestoring = true;
    ACarnivalPlayerCharacter* Rider = CurrentRider;
    AController* Driver = BoardingController.Get();
    CurrentRider = nullptr;
    CurrentSpeed = 0.f;
    BumpVelocity = FVector::ZeroVector;
    ClearControlInputs();
    FTransform ExitTransform = BoardingTransform;
    ExitTransform.SetLocation(ExitLocation);
    Rider->RidePassenger->UnboardRide(ExitTransform);
    if (Driver && (!Driver->GetPawn() || Driver->GetPawn() == this)) Driver->Possess(Rider);
    BoardingController.Reset();
    bRestoring = false;
}

bool ACarnivalBumperCar::TryUnload()
{
    if (!CurrentRider) return true;
    if (!IsStopped()) return false;
    FVector Exit;
    if (!FindExit(Exit, false)) return false;
    RestoreRider(Exit);
    return true;
}

void ACarnivalBumperCar::RequestExit()
{
    if (Arena && CurrentRider) Arena->RequestDriverExit(CurrentRider);
}

void ACarnivalBumperCar::UnPossessed()
{
    ClearControlInputs();
    Super::UnPossessed();
    if (CurrentRider && !bRestoring && GetWorld())
        GetWorld()->GetTimerManager().SetTimerForNextTick(this, &ACarnivalBumperCar::RecoverLostPossession);
}

void ACarnivalBumperCar::RecoverLostPossession()
{
    if (!CurrentRider || GetController()) return;
    FVector Exit;
    if (FindExit(Exit, true)) RestoreRider(Exit);
    else RequestExit();
}

void ACarnivalBumperCar::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (CurrentRider && EndPlayReason == EEndPlayReason::Destroyed)
    {
        FVector Exit;
        if (FindExit(Exit, true)) RestoreRider(Exit);
        else RestoreRider(BoardingTransform.GetLocation());
    }
    Super::EndPlay(EndPlayReason);
}
