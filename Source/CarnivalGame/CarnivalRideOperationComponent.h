#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalRideOperationComponent.generated.h"

class UCarnivalRideControllerComponent;
class USceneComponent;

UENUM(BlueprintType)
enum class ECarnivalOperationState : uint8
{
    Closed, Loading, Securing, Running, Returning, Unloading
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarnivalOperationChanged, ECarnivalOperationState, State);

/** Owns a complete attended cycle while using the vendor ride's start/stop commands. */
UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALGAME_API UCarnivalRideOperationComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCarnivalRideOperationComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride")
    TObjectPtr<AActor> Attendant;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride")
    FName StartFunction = TEXT("StartRide");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride")
    FName StopFunction = TEXT("StopRide");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="0.1"))
    float BoardingSeconds = 5.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="0.1"))
    float SecuringSeconds = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="1.0"))
    float CycleSeconds = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="0.5"))
    float ReturnSeconds = 6.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="0.1"))
    float UnloadingSeconds = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride", meta=(ClampMin="50.0"))
    float InteractionDistance = 350.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ride")
    bool bAllowPlayerOperation = true;

    UPROPERTY(BlueprintReadOnly, Category="Ride")
    ECarnivalOperationState State = ECarnivalOperationState::Closed;
    UPROPERTY(BlueprintReadOnly, Category="Ride")
    TObjectPtr<AActor> PlayerOperator;
    UPROPERTY(BlueprintReadOnly, Category="Ride")
    FString ConfigurationError;
    UPROPERTY(BlueprintReadOnly, Category="Ride")
    int32 CompletedCycles = 0;
    UPROPERTY(BlueprintAssignable, Category="Ride")
    FCarnivalOperationChanged OnStateChanged;

    UFUNCTION(BlueprintCallable, Category="Ride")
    bool InitializeOperation();
    UFUNCTION(BlueprintCallable, Category="Ride")
    bool RequestBoard(AActor* Passenger);
    UFUNCTION(BlueprintCallable, Category="Ride")
    bool RequestPassengerExit(AActor* Passenger);
    UFUNCTION(BlueprintCallable, Category="Ride")
    bool TakeOperatorControl(AActor* Player);
    UFUNCTION(BlueprintCallable, Category="Ride")
    void ReleaseOperatorControl(AActor* Player);
    UFUNCTION(BlueprintCallable, Category="Ride")
    bool OperatorStart(AActor* Player);
    UFUNCTION(BlueprintCallable, Category="Ride")
    bool OperatorStop(AActor* Player);
    UFUNCTION(BlueprintPure, Category="Ride")
    int32 GetPassengerCount() const;
    UFUNCTION(BlueprintPure, Category="Ride")
    bool IsInInteractionRange(AActor* Player) const;
    UFUNCTION(BlueprintPure, Category="Ride")
    bool IsReady() const { return bInitialized && ConfigurationError.IsEmpty(); }
    UFUNCTION(BlueprintCallable, Category="Ride|Inspection")
    static TArray<FString> DescribeRideControls(AActor* Ride);

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;

private:
    struct FMotionPose
    {
        TWeakObjectPtr<USceneComponent> Component;
        FTransform Home;
        FTransform ReturnStart;
    };
    TArray<FMotionPose> MotionPoses;
    UPROPERTY(Transient)
    TObjectPtr<UCarnivalRideControllerComponent> Controller;
    bool bInitialized = false;
    bool bPriorAutoDetect = true;
    bool bActorTickWasEnabled = false;
    float StateSeconds = 0.f;
    bool InvokeCommand(FName Name);
    void ChangeState(ECarnivalOperationState Next);
    void BeginReturn();
    void FreezeMotion();
    void RestorePassengers();
};
