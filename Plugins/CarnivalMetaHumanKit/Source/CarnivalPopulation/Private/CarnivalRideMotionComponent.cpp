#include "CarnivalRideMotionComponent.h"
#include "Components/ActorComponent.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Actor.h"

UCarnivalRideMotionComponent::UCarnivalRideMotionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UCarnivalRideMotionComponent::BeginPlay()
{
    Super::BeginPlay();

    if (!IsValid(MotionSource) && IsValid(GetOwner()))
    {
        AActor* Owner = GetOwner();

        // Prefer a named SceneComponent on the owner (e.g. "MainAnchor" on the Swing).
        if (!MotionSourceName.IsNone())
        {
            TArray<UActorComponent*> Components;
            Owner->GetComponents(Components);
            for (UActorComponent* Component : Components)
            {
                if (Component && Component->GetFName() == MotionSourceName)
                {
                    if (USceneComponent* Scene = Cast<USceneComponent>(Component))
                    {
                        MotionSource = Scene;
                        break;
                    }
                }
            }
        }

        // Fall back to the actor root if no named source matched.
        if (!IsValid(MotionSource))
        {
            MotionSource = Owner->GetRootComponent();
        }
    }
}

void UCarnivalRideMotionComponent::SetMotionSource(USceneComponent* NewMotionSource)
{
    MotionSource = NewMotionSource;
    bHasPreviousSample = false;
}

FCarnivalRideTelemetry UCarnivalRideMotionComponent::GetTelemetry() const
{
    return Telemetry;
}

void UCarnivalRideMotionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!IsValid(MotionSource) || DeltaTime <= KINDA_SMALL_NUMBER)
    {
        return;
    }

    const FTransform CurrentTransform = MotionSource->GetComponentTransform();
    if (!bHasPreviousSample)
    {
        PreviousTransform = CurrentTransform;
        bHasPreviousSample = true;
        return;
    }

    const FVector DeltaLocation = CurrentTransform.GetLocation() - PreviousTransform.GetLocation();
    const FVector Velocity = DeltaLocation / DeltaTime;
    const FVector WorldAcceleration = (Velocity - PreviousVelocity) / DeltaTime;
    const FVector LocalAcceleration = CurrentTransform.InverseTransformVectorNoScale(WorldAcceleration);

    const FQuat DeltaRotation = CurrentTransform.GetRotation() * PreviousTransform.GetRotation().Inverse();
    FVector Axis = FVector::UpVector;
    float AngleRadians = 0.0f;
    DeltaRotation.ToAxisAndAngle(Axis, AngleRadians);
    const float AngularDegreesPerSecond = FMath::RadiansToDegrees(FMath::Abs(FMath::UnwindRadians(AngleRadians))) / DeltaTime;

    Telemetry.Speed = Velocity.Size();
    Telemetry.LinearAcceleration = WorldAcceleration.Size();
    Telemetry.VerticalAcceleration = FMath::Clamp(LocalAcceleration.Z / AccelForMaxIntensity, -1.0f, 1.0f);
    Telemetry.LateralAcceleration = FMath::Clamp(LocalAcceleration.Y / AccelForMaxIntensity, -1.0f, 1.0f);
    Telemetry.AngularSpeed = FMath::Clamp(AngularDegreesPerSecond / AngularSpeedForMaxIntensity, 0.0f, 1.0f);

    const float SpeedScore = FMath::Clamp(Telemetry.Speed / SpeedForMaxIntensity, 0.0f, 1.0f);
    const float AccelScore = FMath::Clamp(Telemetry.LinearAcceleration / AccelForMaxIntensity, 0.0f, 1.0f);
    Telemetry.Intensity = FMath::Clamp(FMath::Max3(SpeedScore, AccelScore, Telemetry.AngularSpeed), 0.0f, 1.0f);

    PreviousTransform = CurrentTransform;
    PreviousVelocity = Velocity;

    OnTelemetryUpdated.Broadcast(Telemetry);
}
