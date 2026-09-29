#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CarnivalBumperCar.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UCarnivalRideSeatComponent;
class UCarnivalBumperArenaComponent;
class ACarnivalPlayerCharacter;

/** Player-driven bumper car; the staffed arena owns when propulsion is enabled. */
UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalBumperCar : public APawn
{
    GENERATED_BODY()
public:
    ACarnivalBumperCar();
    virtual void Tick(float DeltaSeconds) override;
    virtual void UnPossessed() override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UBoxComponent> Hull;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> CarMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UCarnivalRideSeatComponent> DriverSeat;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USpringArmComponent> CameraBoom;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UCameraComponent> FollowCamera;
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite) TObjectPtr<UCarnivalBumperArenaComponent> Arena;
    UPROPERTY(BlueprintReadOnly) TObjectPtr<ACarnivalPlayerCharacter> CurrentRider;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Handling") float MaxSpeed = 550.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Handling") float Acceleration = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Handling") float Braking = 1000.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Handling") float TurnRate = 110.f;
    UPROPERTY(BlueprintReadOnly) float CurrentSpeed = 0.f;
    UFUNCTION(BlueprintCallable) bool CanBoard(ACarnivalPlayerCharacter* Rider) const;
    UFUNCTION(BlueprintCallable) bool Board(ACarnivalPlayerCharacter* Rider);
    UFUNCTION(BlueprintCallable) bool TryUnload();
    UFUNCTION(BlueprintCallable) void RequestExit();
    UFUNCTION(BlueprintCallable) void InputThrottle(float Value);
    UFUNCTION(BlueprintCallable) void InputSteering(float Value);
    UFUNCTION(BlueprintCallable) void InputBrake(float Value);
    UFUNCTION(BlueprintCallable) void ClearControlInputs();
    bool IsStopped() const;
protected:
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
private:
    bool FindExit(FVector& Location, bool bEmergency) const;
    void RestoreRider(const FVector& ExitLocation);
    void RecoverLostPossession();
    FTransform BoardingTransform;
    TWeakObjectPtr<AController> BoardingController;
    FVector BumpVelocity = FVector::ZeroVector;
    float Throttle = 0.f;
    float Steering = 0.f;
    float Brake = 0.f;
    bool bRestoring = false;
};
