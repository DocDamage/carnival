#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "CarnivalTypes.h"
#include "CarnivalRideSeatComponent.generated.h"

UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALPOPULATION_API UCarnivalRideSeatComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    UCarnivalRideSeatComponent();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat")
    FName SeatId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat")
    ECarnivalRestraintType RestraintType = ECarnivalRestraintType::LapBar;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat")
    FTransform PassengerOffset = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat|IK")
    FTransform LeftHandTarget = FTransform(FRotator::ZeroRotator, FVector(25.0, -25.0, 35.0));

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat|IK")
    FTransform RightHandTarget = FTransform(FRotator::ZeroRotator, FVector(25.0, 25.0, 35.0));

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat|IK")
    FTransform LeftFootTarget = FTransform(FRotator::ZeroRotator, FVector(20.0, -12.0, -45.0));

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Carnival|Seat|IK")
    FTransform RightFootTarget = FTransform(FRotator::ZeroRotator, FVector(20.0, 12.0, -45.0));

    UFUNCTION(BlueprintPure, Category="Carnival|Seat")
    bool IsOccupied() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat")
    AActor* GetOccupant() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat")
    FTransform GetPassengerWorldTransform() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat|IK")
    FTransform GetLeftHandWorldTransform() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat|IK")
    FTransform GetRightHandWorldTransform() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat|IK")
    FTransform GetLeftFootWorldTransform() const;

    UFUNCTION(BlueprintPure, Category="Carnival|Seat|IK")
    FTransform GetRightFootWorldTransform() const;

private:
    friend class UCarnivalRidePassengerComponent;

    UPROPERTY(Transient)
    TObjectPtr<AActor> Occupant = nullptr;
};
