#pragma once

#include "CarnivalPlayerCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "CarnivalActivityBase.h"
#include "CarnivalMissionSubsystem.h"
#include "Engine/GameInstance.h"

// Shared collision policy for the two kinematic water/hover vehicles.
namespace CarnivalVehicleExit
{
inline bool IsRecoveryPoseClear(AActor* Vehicle, ACarnivalPlayerCharacter* Rider,
    const UBoxComponent* Hull, const FTransform& Pose)
{
    if (!Vehicle || !Vehicle->GetWorld() || !Hull || Pose.ContainsNaN()) return false;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalVehicleRecovery), false, Vehicle);
    if (Rider) Params.AddIgnoredActor(Rider);
    return !Vehicle->GetWorld()->OverlapBlockingTestByProfile(Pose.GetLocation(), Pose.GetRotation(),
        Hull->GetCollisionProfileName(), FCollisionShape::MakeBox(Hull->GetScaledBoxExtent()), Params);
}

inline void NotifyRecovery(ACarnivalPlayerCharacter* Rider)
{
    if (!Rider) return;
    const bool bCancelled = Rider->ActiveActivity && Rider->ActiveActivity->ActivityState == ECarnivalActivityState::Active;
    if (bCancelled) Rider->ActiveActivity->AbortActivity();
    if (UGameInstance* Instance = Rider->GetGameInstance())
        if (auto* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>())
            Mission->ShowPlayerFeedback(FText::FromString(bCancelled
                ? TEXT("Returned to boarding point. Challenge cancelled.") : TEXT("Returned to boarding point.")));
}

inline bool CanReachSeat(const AActor* Vehicle, const ACarnivalPlayerCharacter* Rider, const FVector& SeatOffset)
{
    if (!IsValid(Rider) || !Vehicle->GetWorld() || Rider->IsParkourTraversing()) return false;
    float Radius, HalfHeight;
    Rider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalVehicleBoarding), false, Vehicle);
    Params.AddIgnoredActor(Rider);
    FHitResult Hit;
    return !Vehicle->GetWorld()->SweepSingleByProfile(Hit, Rider->GetActorLocation(),
        Vehicle->GetActorTransform().TransformPosition(SeatOffset), FQuat::Identity, TEXT("Pawn"),
        FCollisionShape::MakeCapsule(Radius, HalfHeight), Params);
}

inline bool FindGroundExit(AActor* Vehicle, ACarnivalPlayerCharacter* Rider, const FVector& Extent, FVector& OutLocation)
{
    if (!IsValid(Rider) || !Vehicle->GetWorld()) return false;
    float Radius, HalfHeight;
    Rider->GetCapsuleComponent()->GetScaledCapsuleSize(Radius, HalfHeight);
    const auto Capsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalVehicleExit), false, Vehicle);
    Params.AddIgnoredActor(Rider);
    const FVector Right = FRotator(0, Vehicle->GetActorRotation().Yaw, 0).RotateVector(FVector::RightVector);
    const FVector Forward = FRotator(0, Vehicle->GetActorRotation().Yaw, 0).Vector();
    for (const FVector& Offset : {Right * (Extent.Y + Radius + 30.f), -Right * (Extent.Y + Radius + 30.f),
        -Forward * (Extent.X + Radius + 40.f), Right * (Extent.Y + Radius + 120.f), -Right * (Extent.Y + Radius + 120.f)})
    {
        const FVector Probe = Vehicle->GetActorLocation() + Offset;
        FHitResult Floor;
        if (!Vehicle->GetWorld()->LineTraceSingleByChannel(Floor, Probe + FVector(0, 0, 200),
            Probe - FVector(0, 0, 450), ECC_Visibility, Params) || Floor.ImpactNormal.Z < .7f) continue;
        const FVector Candidate = Floor.ImpactPoint + FVector(0, 0, HalfHeight + 2.f);
        FHitResult Path;
        if (Vehicle->GetWorld()->OverlapBlockingTestByProfile(Candidate, FQuat::Identity, TEXT("Pawn"), Capsule, Params)
            || Vehicle->GetWorld()->SweepSingleByProfile(Path, Rider->GetActorLocation(), Candidate,
                FQuat::Identity, TEXT("Pawn"), Capsule, Params)) continue;
        OutLocation = Candidate;
        return true;
    }
    return false;
}
}
