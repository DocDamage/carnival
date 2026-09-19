#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalTypes.h"
#include "CarnivalRideMotionComponent.generated.h"

class USceneComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarnivalTelemetryUpdatedSignature, const FCarnivalRideTelemetry&, Telemetry);

UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALPOPULATION_API UCarnivalRideMotionComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCarnivalRideMotionComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Motion", meta=(ClampMin="1.0"))
    float SpeedForMaxIntensity = 1200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Motion", meta=(ClampMin="1.0"))
    float AccelForMaxIntensity = 2200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Motion", meta=(ClampMin="1.0"))
    float AngularSpeedForMaxIntensity = 180.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Motion", meta=(ToolTip="Name of the owner actor's SceneComponent to sample for motion telemetry. Leave None to use the actor root."))
    FName MotionSourceName = NAME_None;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Motion")
    FCarnivalTelemetryUpdatedSignature OnTelemetryUpdated;

    UFUNCTION(BlueprintCallable, Category="Carnival|Motion")
    void SetMotionSource(USceneComponent* NewMotionSource);

    UFUNCTION(BlueprintPure, Category="Carnival|Motion")
    FCarnivalRideTelemetry GetTelemetry() const;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    UPROPERTY(Transient)
    TObjectPtr<USceneComponent> MotionSource = nullptr;

    FTransform PreviousTransform;
    FVector PreviousVelocity = FVector::ZeroVector;
    FCarnivalRideTelemetry Telemetry;
    bool bHasPreviousSample = false;
};
