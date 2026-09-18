#include "CarnivalRidePassengerComponent.h"
#include "CarnivalPassengerInterface.h"
#include "CarnivalRideSeatComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"

UCarnivalRidePassengerComponent::UCarnivalRidePassengerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
    LastReactionChangeTime = -FLT_MAX;
}

void UCarnivalRidePassengerComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoGeneratePersonality)
    {
        const int32 Seed = PersonalitySeed != 0 ? PersonalitySeed : GetTypeHash(GetOwner()->GetFName());
        GeneratePersonality(Seed);
    }
}

void UCarnivalRidePassengerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (bSnapEveryTick && IsValid(CurrentSeat) && IsValid(GetOwner()))
    {
        GetOwner()->SetActorTransform(CurrentSeat->GetPassengerWorldTransform(), false, nullptr, ETeleportType::TeleportPhysics);
    }
}

bool UCarnivalRidePassengerComponent::BoardRide(AActor* RideActor, UCarnivalRideSeatComponent* Seat)
{
    if (!IsValid(GetOwner()) || !IsValid(RideActor) || !IsValid(Seat) || Seat->IsOccupied() || IsRiding())
    {
        return false;
    }

    CurrentRide = RideActor;
    CurrentSeat = Seat;
    Seat->Occupant = GetOwner();

    GetOwner()->AttachToComponent(Seat, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
    GetOwner()->SetActorTransform(Seat->GetPassengerWorldTransform(), false, nullptr, ETeleportType::TeleportPhysics);

    OnBoarded.Broadcast(RideActor, Seat);

    if (GetOwner()->GetClass()->ImplementsInterface(UCarnivalPassengerInterface::StaticClass()))
    {
        ICarnivalPassengerInterface::Execute_CarnivalRideBoarded(GetOwner(), RideActor, Seat->SeatId, Seat->RestraintType);
    }

    return true;
}

void UCarnivalRidePassengerComponent::UnboardRide(const FTransform& ExitTransform, bool bDetachKeepWorld)
{
    if (!IsRiding() || !IsValid(GetOwner()))
    {
        return;
    }

    AActor* Ride = CurrentRide.Get();
    UCarnivalRideSeatComponent* Seat = CurrentSeat.Get();

    if (IsValid(Seat) && Seat->Occupant == GetOwner())
    {
        Seat->Occupant = nullptr;
    }

    GetOwner()->DetachFromActor(bDetachKeepWorld ? FDetachmentTransformRules::KeepWorldTransform : FDetachmentTransformRules::KeepRelativeTransform);
    GetOwner()->SetActorTransform(ExitTransform, false, nullptr, ETeleportType::TeleportPhysics);

    CurrentRide = nullptr;
    CurrentSeat = nullptr;
    CurrentReaction = ECarnivalRideReaction::Calm;
    LastReactionStrength = 0.0f;
    LastReactionChangeTime = -FLT_MAX;

    OnUnboarded.Broadcast(Ride);

    if (GetOwner()->GetClass()->ImplementsInterface(UCarnivalPassengerInterface::StaticClass()))
    {
        ICarnivalPassengerInterface::Execute_CarnivalRideUnboarded(GetOwner(), Ride);
    }
}

void UCarnivalRidePassengerComponent::ApplyRideTelemetry(const FCarnivalRideTelemetry& Telemetry)
{
    if (!IsRiding())
    {
        return;
    }

    float Strength = 0.0f;
    const ECarnivalRideReaction Reaction = ChooseReaction(Telemetry, Strength);
    SetReaction(Reaction, Strength, Telemetry);
}

void UCarnivalRidePassengerComponent::GeneratePersonality(int32 Seed)
{
    FRandomStream Random(Seed);
    Personality.Archetype = static_cast<ECarnivalGuestArchetype>(Random.RandRange(0, 6));
    Personality.Fear = Random.FRandRange(0.1f, 0.9f);
    Personality.Excitement = Random.FRandRange(0.2f, 1.0f);
    Personality.Showmanship = Random.FRandRange(0.0f, 1.0f);
    Personality.MotionSensitivity = Random.FRandRange(0.0f, 0.9f);

    switch (Personality.Archetype)
    {
        case ECarnivalGuestArchetype::ThrillSeeker:
            Personality.Fear *= 0.4f;
            Personality.Excitement = FMath::Max(Personality.Excitement, 0.8f);
            break;
        case ECarnivalGuestArchetype::Nervous:
            Personality.Fear = FMath::Max(Personality.Fear, 0.75f);
            break;
        case ECarnivalGuestArchetype::ShowOff:
            Personality.Showmanship = FMath::Max(Personality.Showmanship, 0.8f);
            break;
        case ECarnivalGuestArchetype::MotionSensitive:
            Personality.MotionSensitivity = FMath::Max(Personality.MotionSensitivity, 0.8f);
            break;
        case ECarnivalGuestArchetype::Stoic:
            Personality.Fear *= 0.4f;
            Personality.Excitement *= 0.65f;
            break;
        default:
            break;
    }
}

bool UCarnivalRidePassengerComponent::IsRiding() const
{
    return IsValid(CurrentRide) && IsValid(CurrentSeat);
}

UCarnivalRideSeatComponent* UCarnivalRidePassengerComponent::GetCurrentSeat() const
{
    return CurrentSeat.Get();
}

ECarnivalRideReaction UCarnivalRidePassengerComponent::GetCurrentReaction() const
{
    return CurrentReaction;
}

ECarnivalRideReaction UCarnivalRidePassengerComponent::ChooseReaction(const FCarnivalRideTelemetry& Telemetry, float& OutStrength) const
{
    const float Intensity = FMath::Clamp(Telemetry.Intensity, 0.0f, 1.0f);
    const float FearScore = FMath::Clamp(Intensity * (0.5f + Personality.Fear), 0.0f, 1.0f);
    const float ExciteScore = FMath::Clamp(Intensity * (0.45f + Personality.Excitement), 0.0f, 1.0f);
    const float ShowScore = FMath::Clamp(Intensity * Personality.Showmanship, 0.0f, 1.0f);

    if (Intensity < 0.18f)
    {
        OutStrength = 1.0f - Intensity;
        return ECarnivalRideReaction::Calm;
    }

    if (FMath::Abs(Telemetry.LateralAcceleration) > 0.55f)
    {
        OutStrength = FMath::Clamp(FMath::Abs(Telemetry.LateralAcceleration), 0.0f, 1.0f);
        return Telemetry.LateralAcceleration < 0.0f ? ECarnivalRideReaction::LeanLeft : ECarnivalRideReaction::LeanRight;
    }

    if (Telemetry.VerticalAcceleration < -0.55f && ShowScore > 0.45f)
    {
        OutStrength = FMath::Max(ShowScore, Intensity);
        return ECarnivalRideReaction::HandsUp;
    }

    if (FearScore > 0.72f)
    {
        OutStrength = FearScore;
        return ECarnivalRideReaction::Scream;
    }

    if (Telemetry.LinearAcceleration > 0.65f || Telemetry.AngularSpeed > 0.65f)
    {
        OutStrength = Intensity;
        return FearScore > ExciteScore ? ECarnivalRideReaction::Grip : ECarnivalRideReaction::Cheer;
    }

    if (ExciteScore > 0.58f)
    {
        OutStrength = ExciteScore;
        return Personality.Showmanship > 0.55f ? ECarnivalRideReaction::Cheer : ECarnivalRideReaction::Laugh;
    }

    OutStrength = Intensity;
    return ECarnivalRideReaction::Brace;
}

void UCarnivalRidePassengerComponent::SetReaction(ECarnivalRideReaction NewReaction, float Strength, const FCarnivalRideTelemetry& Telemetry)
{
    Strength = FMath::Clamp(Strength, 0.0f, 1.0f);

    const float Now = IsValid(GetWorld()) ? GetWorld()->GetTimeSeconds() : 0.0f;

    if (NewReaction == CurrentReaction)
    {
        // Same reaction: only refresh if strength moved meaningfully, to avoid
        // flooding the AnimBP with tiny per-frame strength updates.
        if (FMath::Abs(Strength - LastReactionStrength) < ReactionStrengthThreshold)
        {
            return;
        }
        LastReactionStrength = Strength;
        OnReactionChanged.Broadcast(NewReaction, Strength, Telemetry);
        if (GetOwner() && GetOwner()->GetClass()->ImplementsInterface(UCarnivalPassengerInterface::StaticClass()))
        {
            ICarnivalPassengerInterface::Execute_CarnivalRideReactionChanged(GetOwner(), NewReaction, Strength, Telemetry);
        }
        return;
    }

    // Different reaction: enforce a minimum hold time so the reaction does not
    // flicker between states on fast-oscillating telemetry (e.g. a swinging ship).
    if (Now - LastReactionChangeTime < MinReactionHoldTime)
    {
        return;
    }

    CurrentReaction = NewReaction;
    LastReactionStrength = Strength;
    LastReactionChangeTime = Now;

    OnReactionChanged.Broadcast(NewReaction, Strength, Telemetry);
    if (GetOwner() && GetOwner()->GetClass()->ImplementsInterface(UCarnivalPassengerInterface::StaticClass()))
    {
        ICarnivalPassengerInterface::Execute_CarnivalRideReactionChanged(GetOwner(), NewReaction, Strength, Telemetry);
    }
}
