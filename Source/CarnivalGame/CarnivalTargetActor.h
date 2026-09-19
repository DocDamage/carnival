// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalTargetActor.generated.h"

class UStaticMeshComponent;
class USphereComponent;
class ACarnivalActivityBase;

UCLASS()
class CARNIVALGAME_API ACarnivalTargetActor : public AActor
{
	GENERATED_BODY()

public:
	ACarnivalTargetActor();

	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* TargetMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USphereComponent* TriggerSphere;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Settings")
	int32 PointValue = 100;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Settings")
	bool bIsRelicOrCollectible = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Target|State")
	bool bIsHit = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Settings")
	ACarnivalActivityBase* OwningActivity;

	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, class AController* EventInstigator, AActor* DamageCauser) override;

	UFUNCTION(BlueprintCallable, Category = "Target")
	void OnCollectedOrHit(AActor* InstigatorActor);

	UFUNCTION(BlueprintCallable, Category = "Target")
	void ResetTarget();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	FVector InitialLocation;
	FRotator InitialRotation;
};

