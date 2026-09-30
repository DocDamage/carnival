#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalBalloonFlightComponent.generated.h"

class UCarnivalRideOperationComponent;
class UStaticMeshComponent;
class UBlueprint;

/** Bounded sightseeing motion for grounded, attended hot-air balloon baskets. */
UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALGAME_API UCarnivalBalloonFlightComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCarnivalBalloonFlightComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Balloon")
    FName MotionComponentName = TEXT("StaticMeshComponent1");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Balloon")
    FName VendorMotionTimelineName = TEXT("HotAirBalloon");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Balloon", meta=(ClampMin="100.0", ClampMax="3000.0"))
    float FlightHeight = 1200.f;
    // Mesh-local split measured from SM_Hotair_Balloon's basket/canopy geometry.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Balloon|Clearance")
    float CanopyStartZ = -350.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Balloon|Clearance", meta=(ClampMin="100.0"))
    float BasketHalfWidth = 250.f;
    UPROPERTY(BlueprintReadOnly, Category="Balloon")
    bool bLastCycleObstructed = false;
    UPROPERTY(Transient, BlueprintReadOnly, Category="Balloon|Clearance")
    FString LastObstruction;
    UPROPERTY(BlueprintReadOnly, Category="Balloon")
    float CurrentLift = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Balloon")
    FString ConfigurationError;

    UFUNCTION(BlueprintCallable, Category="Balloon|Inspection", meta=(DevelopmentOnly))
    static TArray<FString> DescribeBlueprintExecution(UBlueprint* Blueprint);

    /** Editor repair for a project-owned duplicate, never the vendor asset. */
    UFUNCTION(BlueprintCallable, Category="Balloon|Authoring", meta=(DevelopmentOnly))
    static int32 RepairRedundantFireAutoActivation(UBlueprint* Blueprint);

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;

private:
    UPROPERTY(Transient)
    TObjectPtr<UCarnivalRideOperationComponent> Operation;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> MotionSource;
    FTransform LoadingPose;
    float FlightSeconds = 0.f;
    bool bHasLoadingPose = false;
    bool bWasRunning = false;
    bool ResolveComponents();
    bool IsFlightStepClear(const FTransform& Target);
    void StopVendorMotion() const;
    void RequestControlledReturn();
};
