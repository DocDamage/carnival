#include "CarnivalBlueprintLibrary.h"
#include "CarnivalRideSeatComponent.h"

FTransform UCarnivalBlueprintLibrary::GetSeatIKTarget(const UCarnivalRideSeatComponent* Seat, FName TargetName)
{
    if (!IsValid(Seat))
    {
        return FTransform::Identity;
    }

    if (TargetName == TEXT("LeftHand"))
    {
        return Seat->GetLeftHandWorldTransform();
    }
    if (TargetName == TEXT("RightHand"))
    {
        return Seat->GetRightHandWorldTransform();
    }
    if (TargetName == TEXT("LeftFoot"))
    {
        return Seat->GetLeftFootWorldTransform();
    }
    if (TargetName == TEXT("RightFoot"))
    {
        return Seat->GetRightFootWorldTransform();
    }

    return Seat->GetPassengerWorldTransform();
}

float UCarnivalBlueprintLibrary::CalculateRideIntensity(float Speed, float Acceleration, float AngularSpeed, float SpeedMax, float AccelMax, float AngularMax)
{
    const float SpeedScore = FMath::Clamp(Speed / FMath::Max(1.0f, SpeedMax), 0.0f, 1.0f);
    const float AccelScore = FMath::Clamp(Acceleration / FMath::Max(1.0f, AccelMax), 0.0f, 1.0f);
    const float AngularScore = FMath::Clamp(AngularSpeed / FMath::Max(1.0f, AngularMax), 0.0f, 1.0f);
    return FMath::Max3(SpeedScore, AccelScore, AngularScore);
}
