// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalMissionSubsystem.h"
#include "CarnivalMissionInteractionActor.generated.h"

class USphereComponent;
class UPrimitiveComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UTextRenderComponent;
class ACarnivalPlayerCharacter;

UENUM(BlueprintType)
enum class ECarnivalMissionInteraction : uint8
{
	NoticeBoard,
	MansionEntrance,
	FoyerGlove,
	StudyLogAndKey,
	MusicRoomDoor,
	Worker,
	MusicBox,
	MansionExit,
	CarnivalReturn,
	CampaignStation
};

/** Placeable story prop/trigger whose action is guarded by the mission subsystem. */
UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalMissionInteractionActor : public AActor
{
	GENERATED_BODY()

public:
	bool IsSavedDoorOpen() const { return bControlledDoorOpen; }
	bool RestoreSavedDoor(bool bOpen);
	ACarnivalMissionInteractionActor();
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission Interaction")
	TObjectPtr<USphereComponent> InteractionVolume;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction")
	ECarnivalMissionInteraction Interaction = ECarnivalMissionInteraction::NoticeBoard;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mission Interaction|Campaign")
	FName CampaignStationId;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mission Interaction|Campaign", meta=(ClampMin="0", ClampMax="3"))
	int32 CampaignAction = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Target")
	TObjectPtr<AActor> InteractionTargetActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction", meta = (ClampMin = "25.0"))
	float InteractionRadius = 125.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission Interaction")
	TObjectPtr<UStaticMeshComponent> PropVisual;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission Interaction")
	TObjectPtr<UTextRenderComponent> WorldLabel;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	TObjectPtr<UStaticMesh> InteractionMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	FVector InteractionMeshOffset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	FVector InteractionMeshScale = FVector(1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	FText WorldLabelText;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	FVector WorldLabelOffset = FVector(0.0f, 0.0f, 75.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual", meta = (ClampMin = "5.0"))
	float WorldLabelSize = 20.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	FColor WorldLabelColor = FColor(235, 220, 180, 255);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Visual")
	bool bHideVisualWhenConsumed = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Prompt")
	FText PromptOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Feedback")
	FText AcceptedFeedback;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Mission Interaction|Music Room Door")
	TObjectPtr<AActor> ControlledDoorActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Music Room Door")
	FName ControlledDoorActorName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Music Room Door")
	FVector ControlledDoorActorLocation = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Music Room Door", meta = (ClampMin = "1.0", ClampMax = "150.0"))
	float DoorOpenAngleDegrees = 90.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction|Music Room Door", meta = (ClampMin = "0.05"))
	float DoorAnimationSeconds = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission Interaction")
	bool bTriggerOnOverlap = false;

	UFUNCTION(BlueprintPure, Category = "Mission Interaction")
	bool CanInteract(const ACarnivalPlayerCharacter* Player) const;

	UFUNCTION(BlueprintPure, Category = "Mission Interaction")
	FText GetPromptText() const;

	UFUNCTION(BlueprintCallable, Category = "Mission Interaction")
	bool TryInteract(ACarnivalPlayerCharacter* Player);

	UFUNCTION(BlueprintImplementableEvent, Category = "Mission Interaction", meta = (DisplayName = "On Interaction Accepted"))
	void ReceiveInteractionAccepted(ACarnivalPlayerCharacter* Player);

	UFUNCTION(BlueprintImplementableEvent, Category = "Mission Interaction", meta = (DisplayName = "On Interaction Rejected"))
	void ReceiveInteractionRejected(ACarnivalPlayerCharacter* Player, const FText& Reason);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Mission Interaction", meta = (DisplayName = "On Mission State Changed"))
	void ReceiveMissionStateChanged(ECarnivalStoryMissionState NewState, const FText& Objective);

	UFUNCTION()
	void OnPlayerEnteredVolume(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void HandleMissionStateChanged(ECarnivalStoryMissionState NewState, FText Objective);

private:
	UCarnivalMissionSubsystem* GetMissionSubsystem() const;
	bool IsActionAvailable(const UCarnivalMissionSubsystem* Mission) const;
	bool ExecuteMissionAction(ACarnivalPlayerCharacter* Player);
	void ResolveControlledDoorActor();
	void CacheControlledDoorLeaves();
	bool SetControlledDoorOpen(bool bOpen, bool bSnap = false);
	void ApplyVisualSettings();
	void UpdateVisualAvailability(const UCarnivalMissionSubsystem* Mission);
	FText LastActionFailureMessage;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> ControlledDoorLeaves;

	TArray<FRotator> ClosedDoorLeafRotations;
	TArray<FRotator> DoorAnimationStartRotations;
	TArray<FRotator> DoorAnimationTargetRotations;
	float DoorAnimationAge = 0.0f;
	bool bDoorAnimating = false;
	bool bControlledDoorOpen = false;
};
