#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalRideOperationComponent.h"
#include "CarnivalRideAttendant.generated.h"

class UAnimSequence;

/** Dedicated staff actor; its ride operation is independent of roaming crowd actors. */
UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalRideAttendant : public ACharacter
{
    GENERATED_BODY()
public:
    ACarnivalRideAttendant();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    TObjectPtr<AActor> Ride;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    FText RideName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    FName StartFunction = TEXT("StartRide");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    FName StopFunction = TEXT("StopRide");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    float CycleSeconds = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant")
    bool bAllowPlayerOperation = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant|Animation")
    TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Attendant|Animation")
    TObjectPtr<UAnimSequence> OperateAnimation;
    UPROPERTY(BlueprintReadOnly, Category="Attendant")
    TObjectPtr<UCarnivalRideOperationComponent> Operation;
    UFUNCTION(BlueprintCallable, Category="Attendant")
    bool AssignRide(AActor* NewRide);
protected:
    virtual void BeginPlay() override;
    UFUNCTION()
    void HandleRideState(ECarnivalOperationState NewState);
};
