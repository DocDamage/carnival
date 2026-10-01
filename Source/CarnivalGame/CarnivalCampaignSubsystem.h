// Copyright CarnivalMetaHuman. All Rights Reserved.
#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CarnivalCampaignSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FCarnivalInventoryStack
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) FName Item;
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 Count = 0;
};

USTRUCT(BlueprintType)
struct FCarnivalCampaignSnapshot
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) bool bUnlocked = false;
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 CompletedStations = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FCarnivalInventoryStack> Inventory;
};

/** Inspect uses action 0. Relay and route stations require their ordered 1..3 actions. */
struct FCarnivalCampaignStation
{
	FName Id;
	FString Chapter;
	FString Location;
	FString Objective;
	FString Resolution;
	FName Reward;
	FString RewardLabel;
	FString Sequence;
};

/** Session-wide linked campaign and transactional inventory; survives map travel. */
UCLASS()
class CARNIVALGAME_API UCarnivalCampaignSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()
public:
	static const TArray<FCarnivalCampaignStation>& Stations();
	static bool IsValidSnapshot(const FCarnivalCampaignSnapshot& Snapshot);
	// Maps a version-2 (22-station) snapshot onto the current chain; false leaves Out untouched.
	static bool MigrateVersion2(const FCarnivalCampaignSnapshot& Legacy, FCarnivalCampaignSnapshot& Out);
	static int32 ItemLimit(FName Item);
	static bool IsQuestItem(FName Item);
	static FString ItemLabel(FName Item);
	static constexpr int32 SupplySlots = 8;
	// Called by the original mission after a safe rescue/restore, before replay
	// can reset its flags. This retains access even before the first sequel station.
	void UnlockAfterRescue() { State.bUnlocked = true; }

	UFUNCTION(BlueprintPure, Category="Campaign") FCarnivalCampaignSnapshot Capture() const { return State; }
	UFUNCTION(BlueprintCallable, Category="Campaign") bool Restore(const FCarnivalCampaignSnapshot& Snapshot);
	UFUNCTION(BlueprintPure, Category="Campaign") FText GetObjective() const;
	UFUNCTION(BlueprintPure, Category="Campaign") bool IsComplete() const;
	UFUNCTION(BlueprintPure, Category="Inventory") int32 GetItemCount(FName Item) const;
	UFUNCTION(BlueprintPure, Category="Inventory") TArray<FString> GetInventoryLines() const;
	UFUNCTION(BlueprintPure, Category="Campaign") TArray<FString> GetJournalLines() const;
	UFUNCTION(BlueprintPure, Category="Campaign") bool CanUseStation(FName Station) const;
	// Returns true for an accepted puzzle step as well as a completed station.
	UFUNCTION(BlueprintCallable, Category="Campaign") bool UseStation(FName Station, int32 Action);
	// A positive grant is all-or-nothing. Quest tokens are issued only by campaign progress.
	UFUNCTION(BlueprintCallable, Category="Inventory") bool GrantSupply(FName Item, int32 Count);
	UFUNCTION(BlueprintCallable, Category="Inventory") bool SpendSupply(FName Item, int32 Count);
	UPROPERTY(BlueprintReadOnly, Category="Campaign") FString LastResult;
private:
	UPROPERTY() FCarnivalCampaignSnapshot State;
	int32 SequencePosition = 0; // Incomplete puzzles restart safely after loading.
	bool HasRescuedWorker() const;
};
