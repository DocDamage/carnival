// Copyright CarnivalMetaHuman. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CarnivalMissionSubsystem.h"
#include "CarnivalBuildComponent.h"
#include "CarnivalCampaignSubsystem.h"
#include "CarnivalSaveSubsystem.generated.h"

class ACarnivalPlayerCharacter;

USTRUCT()
struct FCarnivalSavedDoor
{
	GENERATED_BODY()
	UPROPERTY(SaveGame) FString ActorId;
	UPROPERTY(SaveGame) bool bOpen = false;
};

UCLASS()
class CARNIVALGAME_API UCarnivalSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UPROPERTY(SaveGame) int32 Version = 3; // 2 = 22-station campaign, migrated on load
	UPROPERTY(SaveGame) int64 Generation = 0;
	UPROPERTY(SaveGame) FDateTime SavedUtc;
	UPROPERTY(SaveGame) FString MapPackage;
	UPROPERTY(SaveGame) FTransform PlayerTransform;
	UPROPERTY(SaveGame) FRotator ViewRotation;
	UPROPERTY(SaveGame) ECarnivalStoryMissionState MissionState = ECarnivalStoryMissionState::FreePlay;
	UPROPERTY(SaveGame) TArray<FCarnivalSavedBuilding> Buildings;
	UPROPERTY(SaveGame) TArray<FCarnivalSavedDoor> Doors;
	UPROPERTY(SaveGame) FCarnivalCampaignSnapshot Campaign;
	bool IsValidSnapshot() const;
};

/** Three independent slots, each with two alternating verified generations. */
UCLASS()
class CARNIVALGAME_API UCarnivalSaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()
public:
	static constexpr int32 SlotCount = 3;
	UFUNCTION(BlueprintCallable, Category="Save")
	bool SaveSlot(int32 Slot, ACarnivalPlayerCharacter* Player);
	UFUNCTION(BlueprintCallable, Category="Save")
	bool LoadSlot(int32 Slot, ACarnivalPlayerCharacter* Player);
	UFUNCTION(BlueprintPure, Category="Save")
	FString GetSlotSummary(int32 Slot) const;
	UPROPERTY(BlueprintReadOnly, Category="Save") FString LastResult;

	// Namespace is fixed for gameplay; tests use unique namespaces and clean up only their own files.
	FString SlotPrefix = TEXT("Carnival_Slot_");
private:
	UCarnivalSaveGame* ReadLatest(int32 Slot, int32& Bank) const;
	bool CheckPlayer(ACarnivalPlayerCharacter* Player);
	FString BankName(int32 Slot, int32 Bank) const;
};
