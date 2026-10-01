// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalActivityTypes.h"
#include "CarnivalActivityBase.generated.h"

class UBoxComponent;
class UTextRenderComponent;
class ACarnivalPlayerCharacter;
class ACarnivalTargetActor;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalActivityBase : public AActor
{
	GENERATED_BODY()

public:
	ACarnivalActivityBase();

	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UBoxComponent* ActivityTrigger;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UTextRenderComponent* PromptText;

	/* Activity Configuration */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	FString ActivityName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	FString LocationName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	ECarnivalChallengeType ActivityType;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	ECarnivalActivityState ActivityState;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	float TimeLimit = 60.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	float TimeRemaining = 60.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	float ElapsedTime = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	int32 CurrentScore = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	int32 TargetScore = 500;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	float GoldTime = 30.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	float SilverTime = 45.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Config")
	float BronzeTime = 60.0f;

	/* Checkpoints for rally / parkour / beacon activities */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Checkpoints")
	TArray<FCarnivalActivityCheckpoint> Checkpoints;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	int32 CurrentCheckpointIndex = 0;

	/* Target actors for combat / shooting / relic hunt */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity|Targets")
	TArray<ACarnivalTargetActor*> Targets;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	ACarnivalPlayerCharacter* ActivePlayer;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity|State")
	bool bPlayerInTrigger = false;

	/* Core API */
	UFUNCTION(BlueprintCallable, Category = "Activity")
	virtual void StartActivity(ACarnivalPlayerCharacter* Player);

	UFUNCTION(BlueprintCallable, Category = "Activity")
	virtual void CompleteActivity(bool bSuccess);

	UFUNCTION(BlueprintCallable, Category = "Activity")
	virtual void AbortActivity();

	UFUNCTION(BlueprintCallable, Category = "Activity")
	virtual void ResetActivity();

	UFUNCTION(BlueprintCallable, Category = "Activity")
	void OnCheckpointReached(int32 CheckpointIndex);

	UFUNCTION(BlueprintCallable, Category = "Activity")
	void OnTargetHit(ACarnivalTargetActor* Target);

	UFUNCTION(BlueprintPure, Category = "Activity")
	FString GetCurrentObjectiveText() const;

	// Legacy placements use their actor identifier as ActivityName.
	UFUNCTION(BlueprintPure, Category = "Activity")
	FString GetDisplayTitle() const;

	UFUNCTION(BlueprintPure, Category = "Activity")
	FString GetMedalRating() const;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnTriggerOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void OnTriggerOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

	void CheckPlayerCheckpoints();
	void UpdateWorldLabel();

	// A target can only contribute once during a run, even if Blueprint repeats a callback.
	TSet<TWeakObjectPtr<ACarnivalTargetActor>> ScoredTargets;
};
