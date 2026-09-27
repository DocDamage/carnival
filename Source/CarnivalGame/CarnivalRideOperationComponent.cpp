#include "CarnivalRideOperationComponent.h"
#include "CarnivalRideControllerComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TimelineComponent.h"
#include "GameFramework/RotatingMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "UObject/UnrealType.h"

UCarnivalRideOperationComponent::UCarnivalRideOperationComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UCarnivalRideOperationComponent::BeginPlay()
{
    Super::BeginPlay();
    // Initialize on the first tick, after vendor Blueprint BeginPlay has run.
}

TArray<FString> UCarnivalRideOperationComponent::DescribeRideControls(AActor* Ride)
{
    TArray<FString> Result;
    if (!IsValid(Ride)) return Result;
    for (TFieldIterator<UFunction> It(Ride->GetClass()); It; ++It)
    {
        const FString Name = It->GetName();
        if (!Name.Contains(TEXT("Ride")) && !Name.Contains(TEXT("Start")) && !Name.Contains(TEXT("Stop"))) continue;
        FString Description = Name + TEXT("(");
        for (TFieldIterator<FProperty> Param(*It); Param && Param->HasAnyPropertyFlags(CPF_Parm); ++Param)
            Description += Param->GetCPPType() + TEXT(" ") + Param->GetName() + TEXT(", ");
        Result.Add(Description + TEXT(")"));
    }
    return Result;
}

bool UCarnivalRideOperationComponent::InvokeCommand(FName Name)
{
    UFunction* Function = IsValid(GetOwner()) ? GetOwner()->FindFunction(Name) : nullptr;
    if (!Function || Function->NumParms != 0) return false;
    GetOwner()->ProcessEvent(Function, nullptr);
    return true;
}

bool UCarnivalRideOperationComponent::InitializeOperation()
{
    if (bInitialized) return IsReady();
    bInitialized = true;
    Controller = GetOwner()->FindComponentByClass<UCarnivalRideControllerComponent>();
    if (!Controller)
    {
        ConfigurationError = TEXT("Missing ride controller");
        return false;
    }
    Controller->RefreshSeats();
    bPriorAutoDetect = Controller->bAutoDetectPhase;
    Controller->bAutoDetectPhase = false;
    Controller->SetRidePhase(ECarnivalRidePhase::Closed);
    UFunction* Start = GetOwner()->FindFunction(StartFunction);
    UFunction* Stop = GetOwner()->FindFunction(StopFunction);
    if (!Start || Start->NumParms || !Stop || Stop->NumParms)
    {
        ConfigurationError = TEXT("Parameterless ride start/stop commands must be configured");
        return false;
    }
    bActorTickWasEnabled = GetOwner()->IsActorTickEnabled();
    TArray<USceneComponent*> Components;
    GetOwner()->GetComponents<USceneComponent>(Components);
    for (USceneComponent* Component : Components)
    {
        if (Component != GetOwner()->GetRootComponent() && Component->Mobility == EComponentMobility::Movable)
            MotionPoses.Add({Component, Component->GetRelativeTransform(), Component->GetRelativeTransform()});
    }
    InvokeCommand(StopFunction);
    FreezeMotion();
    ChangeState(IsValid(Attendant) ? ECarnivalOperationState::Loading : ECarnivalOperationState::Closed);
    return true;
}

void UCarnivalRideOperationComponent::FreezeMotion()
{
    GetOwner()->SetActorTickEnabled(false);
    TArray<URotatingMovementComponent*> Rotators;
    GetOwner()->GetComponents<URotatingMovementComponent>(Rotators);
    for (auto* Component : Rotators) Component->SetComponentTickEnabled(false);
    TArray<UTimelineComponent*> Timelines;
    GetOwner()->GetComponents<UTimelineComponent>(Timelines);
    for (auto* Component : Timelines) Component->Stop();
}

void UCarnivalRideOperationComponent::ChangeState(ECarnivalOperationState Next)
{
    State = Next;
    StateSeconds = 0.f;
    if (Controller)
    {
        ECarnivalRidePhase Phase = ECarnivalRidePhase::Closed;
        switch (State)
        {
        case ECarnivalOperationState::Loading: Phase = ECarnivalRidePhase::Loading; break;
        case ECarnivalOperationState::Securing: Phase = ECarnivalRidePhase::Locked; break;
        case ECarnivalOperationState::Running:
        case ECarnivalOperationState::Returning: Phase = ECarnivalRidePhase::Running; break;
        case ECarnivalOperationState::Unloading: Phase = ECarnivalRidePhase::Unloading; break;
        default: break;
        }
        Controller->SetRidePhase(Phase);
    }
    OnStateChanged.Broadcast(State);
}

bool UCarnivalRideOperationComponent::IsInInteractionRange(AActor* Player) const
{
    return IsValid(Player) && IsValid(Attendant)
        && FVector::DistSquared(Player->GetActorLocation(), Attendant->GetActorLocation()) <= FMath::Square(InteractionDistance);
}

int32 UCarnivalRideOperationComponent::GetPassengerCount() const
{
    int32 Count = 0;
    if (Controller) for (auto* Seat : Controller->GetSeats()) if (Seat->IsOccupied()) ++Count;
    return Count;
}

bool UCarnivalRideOperationComponent::RequestBoard(AActor* Passenger)
{
    if (!IsReady() || State != ECarnivalOperationState::Loading || !IsInInteractionRange(Passenger)
        || PlayerOperator == Passenger || !IsValid(Attendant)) return false;
    const bool bWasEmpty = GetPassengerCount() == 0;
    if (!Controller->BoardPassenger(Passenger)) return false;
    if (bWasEmpty) StateSeconds = 0.f;
    return true;
}

bool UCarnivalRideOperationComponent::RequestPassengerExit(AActor* Passenger)
{
    auto* Component = IsValid(Passenger) ? Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>() : nullptr;
    if (!Component || Component->GetCurrentRide() != GetOwner()) return false;
    if (State == ECarnivalOperationState::Loading || State == ECarnivalOperationState::Securing)
    {
        Component->UnboardRide(Component->GetBoardingTransform());
        if (GetPassengerCount() == 0) ChangeState(ECarnivalOperationState::Loading);
    }
    else if (State == ECarnivalOperationState::Running) BeginReturn();
    return true;
}

bool UCarnivalRideOperationComponent::TakeOperatorControl(AActor* Player)
{
    const auto* Passenger = IsValid(Player) ? Player->FindComponentByClass<UCarnivalRidePassengerComponent>() : nullptr;
    if (!IsReady() || !bAllowPlayerOperation || IsValid(PlayerOperator) || !IsInInteractionRange(Player)
        || !IsValid(Attendant) || (Passenger && Passenger->IsRiding())) return false;
    PlayerOperator = Player;
    return true;
}

void UCarnivalRideOperationComponent::ReleaseOperatorControl(AActor* Player)
{
    if (PlayerOperator != Player) return;
    PlayerOperator = nullptr;
    if (State == ECarnivalOperationState::Loading) StateSeconds = 0.f;
}

bool UCarnivalRideOperationComponent::OperatorStart(AActor* Player)
{
    if (!IsReady() || !IsInInteractionRange(Player) || PlayerOperator != Player || State != ECarnivalOperationState::Loading) return false;
    ChangeState(ECarnivalOperationState::Securing);
    return true;
}

bool UCarnivalRideOperationComponent::OperatorStop(AActor* Player)
{
    if (!IsReady() || !IsInInteractionRange(Player) || PlayerOperator != Player) return false;
    if (State == ECarnivalOperationState::Running) BeginReturn();
    else if (State == ECarnivalOperationState::Securing) ChangeState(ECarnivalOperationState::Loading);
    else return false;
    return true;
}

void UCarnivalRideOperationComponent::BeginReturn()
{
    InvokeCommand(StopFunction);
    FreezeMotion();
    for (auto& Pose : MotionPoses)
        if (Pose.Component.IsValid()) Pose.ReturnStart = Pose.Component->GetRelativeTransform();
    ChangeState(ECarnivalOperationState::Returning);
}

void UCarnivalRideOperationComponent::RestorePassengers()
{
    if (!IsValid(Controller)) return;
    // Each passenger returns to the ground position from which they boarded.
    // This avoids stacking every guest at an unconfigured ride-origin exit.
    for (auto* Seat : Controller->GetSeats())
        if (AActor* Occupant = Seat->GetOccupant())
            if (auto* Passenger = Occupant->FindComponentByClass<UCarnivalRidePassengerComponent>())
                Passenger->UnboardRide(Passenger->GetBoardingTransform());
}

void UCarnivalRideOperationComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!bInitialized) InitializeOperation();
    if (!IsReady()) return;
    if (PlayerOperator && (!IsValid(PlayerOperator) || !IsInInteractionRange(PlayerOperator))) ReleaseOperatorControl(PlayerOperator);
    StateSeconds += DeltaTime;
    switch (State)
    {
    case ECarnivalOperationState::Closed:
        if (IsValid(Attendant)) ChangeState(ECarnivalOperationState::Loading);
        break;
    case ECarnivalOperationState::Loading:
        if (!IsValid(Attendant)) { RestorePassengers(); ChangeState(ECarnivalOperationState::Closed); }
        else if (!IsValid(PlayerOperator) && GetPassengerCount() > 0 && StateSeconds >= FMath::Max(.1f, BoardingSeconds))
            ChangeState(ECarnivalOperationState::Securing);
        break;
    case ECarnivalOperationState::Securing:
        if (!IsValid(Attendant)) { RestorePassengers(); ChangeState(ECarnivalOperationState::Closed); break; }
        if (StateSeconds >= FMath::Max(.1f, SecuringSeconds))
        {
            GetOwner()->SetActorTickEnabled(bActorTickWasEnabled);
            TArray<URotatingMovementComponent*> Rotators;
            GetOwner()->GetComponents<URotatingMovementComponent>(Rotators);
            for (auto* Component : Rotators) Component->SetComponentTickEnabled(true);
            InvokeCommand(StartFunction);
            ChangeState(ECarnivalOperationState::Running);
        }
        break;
    case ECarnivalOperationState::Running:
        if (!IsValid(Attendant) || StateSeconds >= FMath::Max(1.f, CycleSeconds)) BeginReturn();
        break;
    case ECarnivalOperationState::Returning:
    {
        // Return every moving child in local space, so cabins and their passengers
        // remain attached throughout the gentle return to the authored loading pose.
        const float Alpha = FMath::SmoothStep(0.f, 1.f, FMath::Clamp(StateSeconds / FMath::Max(.5f, ReturnSeconds), 0.f, 1.f));
        for (auto& Pose : MotionPoses)
        {
            if (!Pose.Component.IsValid()) continue;
            FTransform Transform;
            Transform.Blend(Pose.ReturnStart, Pose.Home, Alpha);
            Pose.Component->SetRelativeTransform(Transform);
        }
        if (Alpha >= 1.f)
        {
            ++CompletedCycles;
            ChangeState(ECarnivalOperationState::Unloading);
            RestorePassengers();
        }
        break;
    }
    case ECarnivalOperationState::Unloading:
        if (StateSeconds >= FMath::Max(.1f, UnloadingSeconds))
            ChangeState(IsValid(Attendant) ? ECarnivalOperationState::Loading : ECarnivalOperationState::Closed);
        break;
    }
}

void UCarnivalRideOperationComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RestorePassengers();
    if (IsValid(Controller)) Controller->bAutoDetectPhase = bPriorAutoDetect;
    Super::EndPlay(EndPlayReason);
}
