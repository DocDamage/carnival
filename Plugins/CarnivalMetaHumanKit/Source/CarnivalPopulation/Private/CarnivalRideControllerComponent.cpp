#include "CarnivalRideControllerComponent.h"
#include "CarnivalRideMotionComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

UCarnivalRideControllerComponent::UCarnivalRideControllerComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UCarnivalRideControllerComponent::BeginPlay()
{
    Super::BeginPlay();
    RefreshSeats();

    if (AActor* Owner = GetOwner())
    {
        if (UCarnivalRideMotionComponent* Motion = Owner->FindComponentByClass<UCarnivalRideMotionComponent>())
        {
            Motion->OnTelemetryUpdated.AddDynamic(this, &UCarnivalRideControllerComponent::HandleTelemetry);
        }
    }
}

void UCarnivalRideControllerComponent::RefreshSeats()
{
    Seats.Reset();
    if (!IsValid(GetOwner()))
    {
        return;
    }

    TArray<UCarnivalRideSeatComponent*> Found;
    GetOwner()->GetComponents<UCarnivalRideSeatComponent>(Found);
    for (UCarnivalRideSeatComponent* Seat : Found)
    {
        if (IsValid(Seat))
        {
            Seats.Add(Seat);
        }
    }
}

TArray<UCarnivalRideSeatComponent*> UCarnivalRideControllerComponent::GetSeats() const
{
    TArray<UCarnivalRideSeatComponent*> Result;
    Result.Reserve(Seats.Num());
    for (UCarnivalRideSeatComponent* Seat : Seats)
    {
        if (IsValid(Seat))
        {
            Result.Add(Seat);
        }
    }
    return Result;
}

UCarnivalRideSeatComponent* UCarnivalRideControllerComponent::FindAvailableSeat() const
{
    for (UCarnivalRideSeatComponent* Seat : Seats)
    {
        if (IsValid(Seat) && !Seat->IsOccupied())
        {
            return Seat;
        }
    }
    return nullptr;
}

bool UCarnivalRideControllerComponent::BoardPassenger(AActor* Passenger)
{
    if (!IsValid(Passenger) || RidePhase != ECarnivalRidePhase::Loading)
    {
        return false;
    }

    UCarnivalRideSeatComponent* Seat = FindAvailableSeat();
    if (!IsValid(Seat))
    {
        return false;
    }

    if (UCarnivalRidePassengerComponent* PassengerComponent = Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>())
    {
        return PassengerComponent->BoardRide(GetOwner(), Seat);
    }

    return false;
}

void UCarnivalRideControllerComponent::UnboardAllPassengers()
{
    if (!IsValid(GetOwner()))
    {
        return;
    }

    const FTransform ExitWorld = ExitTransform * GetOwner()->GetActorTransform();
    for (UCarnivalRideSeatComponent* Seat : Seats)
    {
        if (!IsValid(Seat) || !Seat->IsOccupied())
        {
            continue;
        }

        AActor* Passenger = Seat->GetOccupant();
        if (!IsValid(Passenger))
        {
            continue;
        }

        if (UCarnivalRidePassengerComponent* PassengerComponent = Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>())
        {
            PassengerComponent->UnboardRide(ExitWorld, true);
        }
    }
}

void UCarnivalRideControllerComponent::SetRidePhase(ECarnivalRidePhase NewPhase)
{
    if (RidePhase == NewPhase)
    {
        return;
    }

    const ECarnivalRidePhase OldPhase = RidePhase;
    RidePhase = NewPhase;
    OnRidePhaseChanged.Broadcast(OldPhase, NewPhase);
}

void UCarnivalRideControllerComponent::PushTelemetryToPassengers(const FCarnivalRideTelemetry& Telemetry)
{
    if (RidePhase != ECarnivalRidePhase::Running)
    {
        return;
    }

    for (UCarnivalRideSeatComponent* Seat : Seats)
    {
        if (!IsValid(Seat) || !Seat->IsOccupied())
        {
            continue;
        }

        if (AActor* Passenger = Seat->GetOccupant())
        {
            if (UCarnivalRidePassengerComponent* PassengerComponent = Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>())
            {
                PassengerComponent->ApplyRideTelemetry(Telemetry);
            }
        }
    }
}

void UCarnivalRideControllerComponent::HandleTelemetry(const FCarnivalRideTelemetry& Telemetry)
{
    // Always forward telemetry to seated passengers (only while Running).
    PushTelemetryToPassengers(Telemetry);

    if (!bAutoDetectPhase)
    {
        return;
    }

    const float DeltaTime = IsValid(GetWorld()) ? GetWorld()->GetDeltaSeconds() : 0.0f;

    switch (RidePhase)
    {
    case ECarnivalRidePhase::Closed:
        // Open the boarding loop automatically.
        SetRidePhase(ECarnivalRidePhase::Loading);
        break;

    case ECarnivalRidePhase::Loading:
    case ECarnivalRidePhase::Locked:
        if (Telemetry.Speed >= MotionStartSpeed)
        {
            SetRidePhase(ECarnivalRidePhase::Running);
            TimeBelowStopThreshold = 0.0f;
        }
        break;

    case ECarnivalRidePhase::Running:
        if (Telemetry.Speed <= MotionStopSpeed)
        {
            TimeBelowStopThreshold += DeltaTime;
            if (TimeBelowStopThreshold >= StopHoldDuration)
            {
                SetRidePhase(ECarnivalRidePhase::Unloading);
                UnboardAllPassengers();
                SetRidePhase(ECarnivalRidePhase::Loading);
                TimeBelowStopThreshold = 0.0f;
            }
        }
        else
        {
            TimeBelowStopThreshold = 0.0f;
        }
        break;

    default:
        break;
    }
}
