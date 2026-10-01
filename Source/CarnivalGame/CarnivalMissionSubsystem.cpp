// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalMissionSubsystem.h"
#include "CarnivalCampaignSubsystem.h"
#include "CarnivalMotorcycle.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Engine/World.h"

namespace
{
void RetainRescueUnlock(UWorld* World)
{
	if (World && World->GetGameInstance())
		if (auto* Campaign = World->GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>()) Campaign->UnlockAfterRescue();
}
}

bool UCarnivalMissionSubsystem::IsSaveableState(ECarnivalStoryMissionState State)
{
	return static_cast<uint8>(State) <= static_cast<uint8>(ECarnivalStoryMissionState::Complete)
		&& State != ECarnivalStoryMissionState::PlayDollScare;
}

bool UCarnivalMissionSubsystem::RestoreSavedState(ECarnivalStoryMissionState State)
{
	if (!IsSaveableState(State)) return false;
	ResetProgress();
	MissionState = State;
	bFoundFoyerGlove = State >= ECarnivalStoryMissionState::SearchStudy;
	bHasServiceKey = State >= ECarnivalStoryMissionState::FindWorker;
	bFoundWorker = State >= ECarnivalStoryMissionState::RecoverMusicBox;
	bRecoveredMusicBox = State >= ECarnivalStoryMissionState::EscapeMansion;
	if (State == ECarnivalStoryMissionState::Complete)
	{
		CompletionMessageEndTime = (GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f) + 8.f;
		RetainRescueUnlock(GetWorld());
	}
	BroadcastCurrentState();
	return true;
}

bool UCarnivalMissionSubsystem::BeginStoryMission()
{
	if (MissionState != ECarnivalStoryMissionState::FreePlay && MissionState != ECarnivalStoryMissionState::Complete)
	{
		return false;
	}

	ResetProgress();
	if (!bHasStoryMotorcycleSnapshot)
	{
		if (UWorld* World = GetWorld())
		{
			bHasStoryMotorcycleSnapshot = true;
			for (TActorIterator<ACarnivalMotorcycle> It(World); It; ++It)
			{
				ACarnivalMotorcycle* Bike = *It;
				if (!IsValid(Bike)) continue;
				FCarnivalStoryMotorcycleSnapshot& Snapshot = StoryMotorcycleSnapshots.AddDefaulted_GetRef();
				Snapshot.BikeClass = Bike->GetClass();
				Snapshot.Transform = Bike->GetActorTransform();
				Snapshot.PhysicsMode = Bike->PhysicsMode;
				Snapshot.Bike = Bike;
			}
		}
	}
	return TransitionTo(ECarnivalStoryMissionState::FindMansion);
}

bool UCarnivalMissionSubsystem::RetryStoryMission()
{
	if (!IsMissionActive() && !IsMissionComplete())
	{
		return false;
	}

	ResetProgress();
	if (UWorld* World = GetWorld())
	{
		if (bHasStoryMotorcycleSnapshot)
		{
			for (FCarnivalStoryMotorcycleSnapshot& Snapshot : StoryMotorcycleSnapshots)
			{
				ACarnivalMotorcycle* Bike = Snapshot.Bike.Get();
				if (!IsValid(Bike) && Snapshot.BikeClass)
				{
					FActorSpawnParameters SpawnParams;
					SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
					Bike = World->SpawnActor<ACarnivalMotorcycle>(Snapshot.BikeClass, Snapshot.Transform, SpawnParams);
					Snapshot.Bike = Bike;
				}
				if (IsValid(Bike))
				{
					Bike->ResetForStoryMissionRetry(Snapshot.Transform, Snapshot.PhysicsMode);
				}
			}
		}
	}
	return TransitionTo(ECarnivalStoryMissionState::FindMansion);
}

bool UCarnivalMissionSubsystem::ReportMansionArrival()
{
	return MissionState == ECarnivalStoryMissionState::FindMansion
		&& TransitionTo(ECarnivalStoryMissionState::SearchFoyer);
}

bool UCarnivalMissionSubsystem::CollectFoyerGlove()
{
	if (MissionState != ECarnivalStoryMissionState::SearchFoyer)
	{
		return false;
	}

	bFoundFoyerGlove = true;
	return TransitionTo(ECarnivalStoryMissionState::SearchStudy);
}

bool UCarnivalMissionSubsystem::CollectStudyLogAndKey()
{
	if (MissionState != ECarnivalStoryMissionState::SearchStudy)
	{
		return false;
	}

	bHasServiceKey = true;
	return TransitionTo(ECarnivalStoryMissionState::FindWorker);
}

bool UCarnivalMissionSubsystem::ReportWorkerFound()
{
	if (MissionState != ECarnivalStoryMissionState::FindWorker || !bHasServiceKey)
	{
		return false;
	}

	bFoundWorker = true;
	return TransitionTo(ECarnivalStoryMissionState::RecoverMusicBox);
}

bool UCarnivalMissionSubsystem::RecoverMusicBox()
{
	if (MissionState != ECarnivalStoryMissionState::RecoverMusicBox || !bFoundWorker)
	{
		return false;
	}

	bRecoveredMusicBox = true;
	return TransitionTo(ECarnivalStoryMissionState::PlayDollScare);
}

bool UCarnivalMissionSubsystem::ReportDollScareComplete()
{
	return MissionState == ECarnivalStoryMissionState::PlayDollScare
		&& bRecoveredMusicBox
		&& TransitionTo(ECarnivalStoryMissionState::EscapeMansion);
}

bool UCarnivalMissionSubsystem::ReportMansionEscaped()
{
	return MissionState == ECarnivalStoryMissionState::EscapeMansion
		&& TransitionTo(ECarnivalStoryMissionState::ReturnToCarnival);
}

bool UCarnivalMissionSubsystem::ReportCarnivalReturned()
{
	if (MissionState != ECarnivalStoryMissionState::ReturnToCarnival)
	{
		return false;
	}

	UWorld* World = GetWorld();
	CompletionMessageEndTime = World ? World->GetTimeSeconds() + 8.0f : 8.0f;
	RetainRescueUnlock(World);
	return TransitionTo(ECarnivalStoryMissionState::Complete);
}

bool UCarnivalMissionSubsystem::CanOpenMusicRoomDoor() const
{
	if (!bHasServiceKey)
	{
		return false;
	}

	switch (MissionState)
	{
	case ECarnivalStoryMissionState::FindWorker:
	case ECarnivalStoryMissionState::RecoverMusicBox:
	case ECarnivalStoryMissionState::PlayDollScare:
	case ECarnivalStoryMissionState::EscapeMansion:
	case ECarnivalStoryMissionState::ReturnToCarnival:
	case ECarnivalStoryMissionState::Complete:
		return true;
	default:
		return false;
	}
}

void UCarnivalMissionSubsystem::ShowPlayerFeedback(FText Message, float DurationSeconds)
{
	PlayerFeedback = MoveTemp(Message);
	const UWorld* World = GetWorld();
	PlayerFeedbackEndTime = (World ? World->GetTimeSeconds() : 0.0f) + FMath::Max(0.0f, DurationSeconds);
}

FText UCarnivalMissionSubsystem::GetPlayerFeedback() const
{
	const UWorld* World = GetWorld();
	return World && World->GetTimeSeconds() <= PlayerFeedbackEndTime
		? PlayerFeedback
		: FText::GetEmpty();
}

FText UCarnivalMissionSubsystem::GetCurrentObjective() const
{
	switch (MissionState)
	{
	case ECarnivalStoryMissionState::FindMansion:
		return FText::FromString(TEXT("Follow the coastal road to the mansion."));
	case ECarnivalStoryMissionState::SearchFoyer:
		return FText::FromString(TEXT("Search the foyer for the worker's trail."));
	case ECarnivalStoryMissionState::SearchStudy:
		return FText::FromString(TEXT("Check the study for the music-room key."));
	case ECarnivalStoryMissionState::FindWorker:
		return FText::FromString(TEXT("Use the service key. Find Eli in the music room."));
	case ECarnivalStoryMissionState::RecoverMusicBox:
		return FText::FromString(TEXT("Eli is safe. Take the music box beside the doll."));
	case ECarnivalStoryMissionState::PlayDollScare:
		return FText::FromString(TEXT("The doll is moving. Stay clear and leave by the foyer."));
	case ECarnivalStoryMissionState::EscapeMansion:
		return FText::FromString(TEXT("Leave the mansion through the foyer."));
	case ECarnivalStoryMissionState::ReturnToCarnival:
		return FText::FromString(TEXT("Return to the Carnival by the coastal road."));
	case ECarnivalStoryMissionState::Complete:
	{
		UWorld* World = GetWorld();
		if (World && World->GetTimeSeconds() <= CompletionMessageEndTime)
		{
			return FText::FromString(TEXT("Worker found. Music box recovered. Carnival free play is open."));
		}
		return FText::GetEmpty();
	}
	case ECarnivalStoryMissionState::FreePlay:
	default:
		return FText::GetEmpty();
	}
}

bool UCarnivalMissionSubsystem::IsMissionActive() const
{
	return MissionState != ECarnivalStoryMissionState::FreePlay
		&& MissionState != ECarnivalStoryMissionState::Complete;
}

bool UCarnivalMissionSubsystem::TransitionTo(ECarnivalStoryMissionState NewState)
{
	if (MissionState == NewState)
	{
		return false;
	}

	MissionState = NewState;
	BroadcastCurrentState();
	return true;
}

void UCarnivalMissionSubsystem::ResetProgress()
{
	bFoundFoyerGlove = false;
	bHasServiceKey = false;
	bFoundWorker = false;
	bRecoveredMusicBox = false;
	CompletionMessageEndTime = 0.0f;
	PlayerFeedback = FText::GetEmpty();
	PlayerFeedbackEndTime = 0.0f;
}

void UCarnivalMissionSubsystem::BroadcastCurrentState()
{
	OnMissionChanged.Broadcast(MissionState, GetCurrentObjective());
}
