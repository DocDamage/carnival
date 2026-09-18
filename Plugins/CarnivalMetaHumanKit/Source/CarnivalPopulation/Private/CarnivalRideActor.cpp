#include "CarnivalRideActor.h"
#include "CarnivalRideMotionComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/SceneComponent.h"

ACarnivalRideActor::ACarnivalRideActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    MotionTelemetry = CreateDefaultSubobject<UCarnivalRideMotionComponent>(TEXT("MotionTelemetry"));
}

void ACarnivalRideActor::BeginPlay()
{
    Super::BeginPlay();
    RefreshSeats();

    if (IsValid(MotionTelemetry))
    {
        MotionTelemetry->OnTelemetryUpdated.AddDynamic(this, &ACarnivalRideActor::PushTelemetryToPassengers);
    }
}

void ACarnivalRideActor::RefreshSeats()
{
    Seats.Reset();
    TArray<UCarnivalRideSeatComponent*> Found;
    GetComponents<UCarnivalRideSeatComponent>(Found);
    for (UCarnivalRideSeatComponent* Seat : Found)
    {
        if (IsValid(Seat))
        {
            Seats.Add(Seat);
        }
    }
}

TArray<UCarnivalRideSeatComponent*> ACarnivalRideActor::GetSeats() const
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

UCarnivalRideSeatComponent* ACarnivalRideActor::FindAvailableSeat() const
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

bool ACarnivalRideActor::BoardPassenger(AActor* Passenger)
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

    UCarnivalRidePassengerComponent* PassengerComponent = Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>();
    if (!IsValid(PassengerComponent))
    {
        return false;
    }

    return PassengerComponent->BoardRide(this, Seat);
}

void ACarnivalRideActor::UnboardAllPassengers()
{
    const FTransform ExitWorld = ExitTransform * GetActorTransform();
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

void ACarnivalRideActor::SetRidePhase(ECarnivalRidePhase NewPhase)
{
    if (RidePhase == NewPhase)
    {
        return;
    }

    const ECarnivalRidePhase OldPhase = RidePhase;
    RidePhase = NewPhase;
    OnRidePhaseChanged.Broadcast(OldPhase, NewPhase);
}

void ACarnivalRideActor::PushTelemetryToPassengers(const FCarnivalRideTelemetry& Telemetry)
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

        AActor* Passenger = Seat->GetOccupant();
        if (IsValid(Passenger))
        {
            if (UCarnivalRidePassengerComponent* PassengerComponent = Passenger->FindComponentByClass<UCarnivalRidePassengerComponent>())
            {
                PassengerComponent->ApplyRideTelemetry(Telemetry);
            }
        }
    }
}
