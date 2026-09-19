// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "CarnivalActivityTypes.generated.h"

UENUM(BlueprintType)
enum class ECarnivalChallengeType : uint8
{
	StuntRally			UMETA(DisplayName = "Stunt Rally"),
	TimeTrial			UMETA(DisplayName = "Time Trial"),
	TargetShooting		UMETA(DisplayName = "Target Shooting"),
	MeleeTrial			UMETA(DisplayName = "Melee Trial"),
	ParkourRush			UMETA(DisplayName = "Parkour Rush"),
	RelicHunt			UMETA(DisplayName = "Relic Hunt"),
	BeaconClimb			UMETA(DisplayName = "Beacon Climb & Dive")
};

UENUM(BlueprintType)
enum class ECarnivalActivityState : uint8
{
	Inactive			UMETA(DisplayName = "Inactive"),
	Active				UMETA(DisplayName = "Active"),
	Completed			UMETA(DisplayName = "Completed"),
	Failed				UMETA(DisplayName = "Failed")
};

USTRUCT(BlueprintType)
struct FCarnivalActivityCheckpoint
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity")
	float Radius = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Activity")
	FString Description = TEXT("Checkpoint");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Activity")
	bool bReached = false;
};
