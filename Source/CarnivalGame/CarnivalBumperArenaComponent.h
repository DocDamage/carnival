#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalBumperArenaComponent.generated.h"

class ACarnivalBumperCar;
class ACarnivalPlayerCharacter;
class UCarnivalRideOperationComponent;

/** Keeps the bumper driving session inside the measured arena and staffed cycle. */
UCLASS(ClassGroup=(Carnival), meta=(BlueprintSpawnableComponent))
class CARNIVALGAME_API UCarnivalBumperArenaComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Arena") TArray<TObjectPtr<ACarnivalBumperCar>> Cars;
    /** Explicit vendor display cars replaced by Cars; applied after Blueprint BeginPlay. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Arena") TArray<FName> ReplacedDisplayCarComponents;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Arena") FVector LocalCenter = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Arena") FVector2D HalfExtent = FVector2D(900, 700);
    UFUNCTION(BlueprintCallable) bool InitializeArena();
    UFUNCTION(BlueprintCallable) bool BoardPlayer(ACarnivalPlayerCharacter* Player);
    UFUNCTION(BlueprintPure) int32 GetDriverCount() const;
    UFUNCTION(BlueprintPure) bool IsDrivingEnabled() const;
    UFUNCTION(BlueprintPure) bool AreCarsStopped() const;
    UFUNCTION(BlueprintCallable) bool TryUnloadAll();
    UFUNCTION(BlueprintCallable) void RequestDriverExit(ACarnivalPlayerCharacter* Player);
    UFUNCTION(BlueprintPure) bool ContainsCarLocation(FVector WorldLocation, float Radius) const;
    UCarnivalRideOperationComponent* GetOperation() const;
    ACarnivalBumperCar* FindDriverCar(const AActor* Player) const;
    void ClearInputs();
};
