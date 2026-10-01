// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalMissionSubsystem.generated.h"

class ACarnivalMotorcycle;

UENUM(BlueprintType)
enum class ECarnivalStoryMissionState : uint8
{
	FreePlay UMETA(DisplayName = "Carnival Free Play"),
	FindMansion UMETA(DisplayName = "Find the Mansion"),
	SearchFoyer UMETA(DisplayName = "Search the Foyer"),
	SearchStudy UMETA(DisplayName = "Search the Study"),
	FindWorker UMETA(DisplayName = "Find the Worker"),
	RecoverMusicBox UMETA(DisplayName = "Recover the Music Box"),
	PlayDollScare UMETA(DisplayName = "Doll Encounter"),
	EscapeMansion UMETA(DisplayName = "Leave the Mansion"),
	ReturnToCarnival UMETA(DisplayName = "Return to the Carnival"),
	Complete UMETA(DisplayName = "Story Complete")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCarnivalStoryMissionChanged, ECarnivalStoryMissionState, NewState, FText, Objective);

USTRUCT()
struct FCarnivalStoryMotorcycleSnapshot
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TSubclassOf<ACarnivalMotorcycle> BikeClass;

	UPROPERTY(Transient)
	FTransform Transform;

	UPROPERTY(Transient)
	EMotorcyclePhysicsMode PhysicsMode = EMotorcyclePhysicsMode::Arcade;

	TWeakObjectPtr<ACarnivalMotorcycle> Bike;
};

/** Session-level state for the missing-worker and music-box story. Placed interactions call these guarded transitions. */
UCLASS()
class CARNIVALGAME_API UCarnivalMissionSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// Save files contain a stable story stage; transient scare playback is never serialized.
	static bool IsSaveableState(ECarnivalStoryMissionState State);
	bool RestoreSavedState(ECarnivalStoryMissionState State);

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool BeginStoryMission();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool RetryStoryMission();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool ReportMansionArrival();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool CollectFoyerGlove();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool CollectStudyLogAndKey();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool ReportWorkerFound();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool RecoverMusicBox();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool ReportDollScareComplete();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool ReportMansionEscaped();

	UFUNCTION(BlueprintCallable, Category = "Story Mission")
	bool ReportCarnivalReturned();

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	bool CanOpenMusicRoomDoor() const;

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	FText GetCurrentObjective() const;

	UFUNCTION(BlueprintCallable, Category = "Story Mission|Feedback")
	void ShowPlayerFeedback(FText Message, float DurationSeconds = 3.0f);

	UFUNCTION(BlueprintPure, Category = "Story Mission|Feedback")
	FText GetPlayerFeedback() const;

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	bool IsMissionActive() const;

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	bool IsMissionComplete() const { return MissionState == ECarnivalStoryMissionState::Complete; }

	UFUNCTION(BlueprintPure, Category = "Story Mission")
	ECarnivalStoryMissionState GetMissionState() const { return MissionState; }

	UPROPERTY(BlueprintAssignable, Category = "Story Mission")
	FOnCarnivalStoryMissionChanged OnMissionChanged;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Story Mission|Progress")
	ECarnivalStoryMissionState MissionState = ECarnivalStoryMissionState::FreePlay;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Story Mission|Progress")
	bool bFoundFoyerGlove = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Story Mission|Progress")
	bool bHasServiceKey = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Story Mission|Progress")
	bool bFoundWorker = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Story Mission|Progress")
	bool bRecoveredMusicBox = false;

private:
	bool TransitionTo(ECarnivalStoryMissionState NewState);
	void ResetProgress();
	void BroadcastCurrentState();

	UPROPERTY(Transient)
	TArray<FCarnivalStoryMotorcycleSnapshot> StoryMotorcycleSnapshots;
	bool bHasStoryMotorcycleSnapshot = false;

	float CompletionMessageEndTime = 0.0f;
	FText PlayerFeedback;
	float PlayerFeedbackEndTime = 0.0f;
};
