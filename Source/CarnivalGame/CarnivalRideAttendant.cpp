#include "CarnivalRideAttendant.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

ACarnivalRideAttendant::ACarnivalRideAttendant()
{
    PrimaryActorTick.bCanEverTick = false;
    GetCapsuleComponent()->InitCapsuleSize(34.f, 90.f);
    GetMesh()->SetRelativeLocation(FVector(0, 0, -90));
    GetMesh()->SetRelativeRotation(FRotator(0, -90, 0));
    GetCharacterMovement()->bOrientRotationToMovement = false;
    bUseControllerRotationYaw = false;
    RideName = FText::FromString(TEXT("Carnival ride"));
}

void ACarnivalRideAttendant::BeginPlay()
{
    Super::BeginPlay();
    AssignRide(Ride);
    HandleRideState(IsValid(Operation) ? Operation->State : ECarnivalOperationState::Closed);
}

void ACarnivalRideAttendant::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (IsValid(Operation))
    {
        Operation->OnStateChanged.RemoveDynamic(this, &ACarnivalRideAttendant::HandleRideState);
        if (Operation->Attendant == this)
        {
            Operation->ReleaseOperatorControl(Operation->PlayerOperator);
            Operation->Attendant = nullptr;
        }
    }
    Super::EndPlay(EndPlayReason);
}

bool ACarnivalRideAttendant::AssignRide(AActor* NewRide)
{
    if (!IsValid(NewRide)) return false;
    auto* Existing = NewRide->FindComponentByClass<UCarnivalRideOperationComponent>();
    if (Existing && IsValid(Existing->Attendant) && Existing->Attendant != this) return false;
    if (IsValid(Operation) && Operation != Existing)
    {
        Operation->OnStateChanged.RemoveDynamic(this, &ACarnivalRideAttendant::HandleRideState);
        if (Operation->Attendant == this)
        {
            Operation->ReleaseOperatorControl(Operation->PlayerOperator);
            Operation->Attendant = nullptr;
        }
    }
    Ride = NewRide;
    Operation = Existing ? Existing : NewObject<UCarnivalRideOperationComponent>(NewRide);
    Operation->Attendant = this;
    Operation->Experience = Experience;
    Operation->StartFunction = StartFunction;
    Operation->StopFunction = StopFunction;
    Operation->CycleSeconds = CycleSeconds;
    Operation->bAllowPlayerOperation = bAllowPlayerOperation;
    Operation->OnStateChanged.AddUniqueDynamic(this, &ACarnivalRideAttendant::HandleRideState);
    if (!Existing)
    {
        NewRide->AddInstanceComponent(Operation);
        Operation->RegisterComponent();
    }
    HandleRideState(Operation->State);
    return true;
}

void ACarnivalRideAttendant::HandleRideState(ECarnivalOperationState NewState)
{
    const bool bOperating = NewState == ECarnivalOperationState::Securing || NewState == ECarnivalOperationState::Returning;
    UAnimSequence* Clip = bOperating && OperateAnimation ? OperateAnimation.Get() : IdleAnimation.Get();
    if (Clip) GetMesh()->PlayAnimation(Clip, !bOperating);
}
