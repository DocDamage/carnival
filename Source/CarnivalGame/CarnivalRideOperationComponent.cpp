#include "CarnivalRideOperationComponent.h"
#include "CarnivalRideControllerComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TimelineComponent.h"
#include "GameFramework/RotatingMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "UObject/UnrealType.h"
#include "CarnivalBumperArenaComponent.h"
#include "CarnivalBumperCar.h"
#include "CarnivalPlayerCharacter.h"

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

TArray<FString> UCarnivalRideOperationComponent::DescribeRideProperties(AActor* Ride)
{
    TArray<FString> Result;
    if (!IsValid(Ride)) return Result;
    for (TFieldIterator<FProperty> It(Ride->GetClass()); It; ++It)
    {
        const FString Name = It->GetName();
        const FString Lower = Name.ToLower();
        if (!Lower.Contains(TEXT("ride")) && !Lower.Contains(TEXT("cycle")) && !Lower.Contains(TEXT("state"))
            && !Lower.Contains(TEXT("auto")) && !Lower.Contains(TEXT("power")) && !Lower.Contains(TEXT("enable"))
            && !Lower.Contains(TEXT("random")) && !Lower.Contains(TEXT("volume"))
            && !Lower.Contains(TEXT("music")) && !Lower.Contains(TEXT("sound"))) continue;
        FString Value;
        It->ExportTextItem_Direct(Value, It->ContainerPtrToValuePtr<void>(Ride), nullptr, Ride, PPF_None);
        Result.Add(Name + TEXT(" = ") + Value.Left(4096));
    }
    TArray<UActorComponent*> Components;
    Ride->GetComponents<UActorComponent>(Components);
    for (const auto* Component : Components)
        Result.Add(FString::Printf(TEXT("Component %s [%s] active=%d tick=%d"), *Component->GetName(),
            *Component->GetClass()->GetName(), Component->IsActive(), Component->IsComponentTickEnabled()));
    return Result;
}

bool UCarnivalRideOperationComponent::IsReady() const
{
    return bInitialized && IsValid(Controller) && ConfigurationError.IsEmpty();
}

bool UCarnivalRideOperationComponent::InitializeOperation()
{
    if (IsReady()) return true;
    // A failed initialization can be retried explicitly after authoring/assigning
    // components. Do not leave a corrected ride permanently closed.
    const bool bFirstAttempt = !bInitialized;
    bInitialized = true;
    ConfigurationError.Reset();
    if (!IsValid(GetOwner())) return false;
    Controller = GetOwner()->FindComponentByClass<UCarnivalRideControllerComponent>();
    if (!Controller)
    {
        ConfigurationError = TEXT("Missing ride controller");
        return false;
    }
    Controller->RefreshSeats();
    if (bFirstAttempt || !bControllerClaimed) bPriorAutoDetect = Controller->bAutoDetectPhase;
    bControllerClaimed = true;
    Controller->bAutoDetectPhase = false;
    Controller->SetRidePhase(ECarnivalRidePhase::Closed);
    if (Experience == ECarnivalRideExperience::SeatedRide && Controller->GetSeats().IsEmpty())
    {
        ConfigurationError = TEXT("No passenger seats have been authored for this ride");
        return false;
    }
    TSet<FName> SeatIds;
    for (const auto* Seat : Controller->GetSeats())
    {
        if (Seat->SeatId.IsNone() || SeatIds.Contains(Seat->SeatId))
        {
            ConfigurationError = TEXT("Passenger seats require unique, nonempty SeatIds");
            return false;
        }
        SeatIds.Add(Seat->SeatId);
    }
    UFunction* Start = GetOwner()->FindFunction(StartFunction);
    UFunction* Stop = GetOwner()->FindFunction(StopFunction);
    if (Experience == ECarnivalRideExperience::DrivingArena)
    {
        auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>();
        if (!Arena || !Arena->InitializeArena())
        {
            ConfigurationError = TEXT("Driving arena requires configured bounds and bumper cars");
            return false;
        }
    }
    else if (!Start || Start->NumParms || !Stop || Stop->NumParms)
    {
        ConfigurationError = TEXT("Parameterless ride start/stop commands must be configured");
        return false;
    }
    bActorTickWasEnabled = GetOwner()->IsActorTickEnabled();
    TArray<USceneComponent*> Components;
    GetOwner()->GetComponents<USceneComponent>(Components);
    for (USceneComponent* Component : Components)
    {
        if (Component->Mobility == EComponentMobility::Movable)
            MotionPoses.Add({Component, Component->GetRelativeTransform(), Component->GetRelativeTransform()});
    }
    TArray<UActorComponent*> ActorComponents;
    GetOwner()->GetComponents<UActorComponent>(ActorComponents);
    for (UActorComponent* Component : ActorComponents)
    {
        if (Component != this && (Component->IsA<URotatingMovementComponent>()
            || AdditionalMotionComponentNames.Contains(Component->GetFName())))
            MotionTicks.Add({Component, Component->IsComponentTickEnabled()});
    }
    if (Experience != ECarnivalRideExperience::DrivingArena) InvokeCommand(StopFunction);
    FreezeMotion();
    ChangeState(IsValid(Attendant) ? ECarnivalOperationState::Loading : ECarnivalOperationState::Closed);
    return true;
}

void UCarnivalRideOperationComponent::FreezeMotion()
{
    GetOwner()->SetActorTickEnabled(false);
    for (const auto& Motion : MotionTicks)
        if (Motion.Component.IsValid()) Motion.Component->SetComponentTickEnabled(false);
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
    if (Experience == ECarnivalRideExperience::DrivingArena)
        if (auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>()) return Arena->GetDriverCount();
    int32 Count = 0;
    if (Controller) for (auto* Seat : Controller->GetSeats()) if (Seat->IsOccupied()) ++Count;
    return Count;
}

bool UCarnivalRideOperationComponent::RequestBoard(AActor* Passenger)
{
    if (!IsReady() || State != ECarnivalOperationState::Loading || !IsInInteractionRange(Passenger)
        || PlayerOperator == Passenger || !IsValid(Attendant)) return false;
    if (Experience == ECarnivalRideExperience::DrivingArena)
    {
        auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>();
        const bool bWasEmpty = GetPassengerCount() == 0;
        if (!Arena || !Arena->BoardPlayer(Cast<ACarnivalPlayerCharacter>(Passenger))) return false;
        if (bWasEmpty) StateSeconds = 0.f;
        return true;
    }
    if (Experience != ECarnivalRideExperience::SeatedRide)
    {
        // Visitors trigger the staffed show/attraction but remain on foot and
        // may use its doors and return route throughout the timed cycle.
        if (IsValid(PlayerOperator)) return false;
        ChangeState(ECarnivalOperationState::Securing);
        return true;
    }
    const bool bWasEmpty = GetPassengerCount() == 0;
    if (!Controller->BoardPassenger(Passenger)) return false;
    if (bWasEmpty) StateSeconds = 0.f;
    return true;
}

bool UCarnivalRideOperationComponent::RequestPassengerExit(AActor* Passenger)
{
    if (!IsReady()) return false;
    if (Experience == ECarnivalRideExperience::DrivingArena)
    {
        auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>();
        auto* Car = Arena ? Arena->FindDriverCar(Passenger) : nullptr;
        if (!Car) return false;
        if (State == ECarnivalOperationState::Loading || State == ECarnivalOperationState::Securing)
        {
            Car->TryUnload();
            if (GetPassengerCount() == 0) ChangeState(ECarnivalOperationState::Loading);
        }
        else if (State == ECarnivalOperationState::Running) BeginReturn();
        return true;
    }
    auto* Component = IsValid(Passenger) ? Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>() : nullptr;
    if (!Component || Component->GetCurrentRide() != GetOwner()) return false;
    if (State == ECarnivalOperationState::Loading || State == ECarnivalOperationState::Securing)
    {
        if (Component->CanUnboardAt(Component->GetBoardingTransform()))
            Component->UnboardRide(Component->GetBoardingTransform());
        else ChangeState(ECarnivalOperationState::Unloading);
        if (GetPassengerCount() == 0)
            ChangeState(IsValid(Attendant) ? ECarnivalOperationState::Loading : ECarnivalOperationState::Closed);
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
    if (Experience == ECarnivalRideExperience::DrivingArena)
    {
        if (auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>()) Arena->ClearInputs();
    }
    else InvokeCommand(StopFunction);
    FreezeMotion();
    for (auto& Pose : MotionPoses)
        if (Pose.Component.IsValid()) Pose.ReturnStart = Pose.Component->GetRelativeTransform();
    ChangeState(ECarnivalOperationState::Returning);
}

void UCarnivalRideOperationComponent::RestorePassengers(bool bForceForTeardown)
{
    if (Experience == ECarnivalRideExperience::DrivingArena)
    {
        if (auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>()) Arena->TryUnloadAll();
        return;
    }
    if (!IsValid(Controller)) return;
    // Each passenger returns to the ground position from which they boarded.
    // This avoids stacking every guest at an unconfigured ride-origin exit.
    for (auto* Seat : Controller->GetSeats())
        if (AActor* Occupant = Seat->GetOccupant())
            if (auto* Passenger = Occupant->FindComponentByClass<UCarnivalRidePassengerComponent>())
                if (bForceForTeardown || Passenger->CanUnboardAt(Passenger->GetBoardingTransform()))
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
        RestorePassengers();
        if (GetPassengerCount() == 0 && IsValid(Attendant)) ChangeState(ECarnivalOperationState::Loading);
        break;
    case ECarnivalOperationState::Loading:
        if (!IsValid(Attendant)) { RestorePassengers(); ChangeState(GetPassengerCount() > 0 ? ECarnivalOperationState::Unloading : ECarnivalOperationState::Closed); }
        else if (!IsValid(PlayerOperator) && GetPassengerCount() > 0 && StateSeconds >= FMath::Max(.1f, BoardingSeconds))
            ChangeState(ECarnivalOperationState::Securing);
        break;
    case ECarnivalOperationState::Securing:
        if (!IsValid(Attendant)) { RestorePassengers(); ChangeState(GetPassengerCount() > 0 ? ECarnivalOperationState::Unloading : ECarnivalOperationState::Closed); break; }
        if (StateSeconds >= FMath::Max(.1f, SecuringSeconds))
        {
            if (Experience != ECarnivalRideExperience::DrivingArena)
            {
                GetOwner()->SetActorTickEnabled(bActorTickWasEnabled);
                for (const auto& Motion : MotionTicks)
                    if (Motion.Component.IsValid()) Motion.Component->SetComponentTickEnabled(Motion.bWasEnabled);
                InvokeCommand(StartFunction);
            }
            ChangeState(ECarnivalOperationState::Running);
        }
        break;
    case ECarnivalOperationState::Running:
        if (!IsValid(Attendant) || StateSeconds >= FMath::Max(1.f, CycleSeconds)) BeginReturn();
        break;
    case ECarnivalOperationState::Returning:
    {
        if (Experience == ECarnivalRideExperience::DrivingArena)
        {
            auto* Arena = GetOwner()->FindComponentByClass<UCarnivalBumperArenaComponent>();
            if (Arena && Arena->AreCarsStopped())
            {
                ++CompletedCycles;
                ChangeState(ECarnivalOperationState::Unloading);
                RestorePassengers();
            }
            break;
        }
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
        // Keep occupied seats and retry until the original ground exits clear.
        // Reopening while a passenger remains would start another unwanted cycle.
        RestorePassengers();
        if (GetPassengerCount() > 0) break;
        if (StateSeconds >= FMath::Max(.1f, UnloadingSeconds))
            ChangeState(IsValid(Attendant) ? ECarnivalOperationState::Loading : ECarnivalOperationState::Closed);
        break;
    }
}

void UCarnivalRideOperationComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RestorePassengers(true);
    if (bControllerClaimed && IsValid(Controller)) Controller->bAutoDetectPhase = bPriorAutoDetect;
    Super::EndPlay(EndPlayReason);
}
