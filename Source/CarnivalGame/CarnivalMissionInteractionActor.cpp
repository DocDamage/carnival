// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalMissionInteractionActor.h"

#include "CarnivalMissionSubsystem.h"
#include "CarnivalCampaignSubsystem.h"
#include "CarnivalHauntedDoll.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "CollisionQueryParams.h"

ACarnivalMissionInteractionActor::ACarnivalMissionInteractionActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	InteractionVolume = CreateDefaultSubobject<USphereComponent>(TEXT("InteractionVolume"));
	RootComponent = InteractionVolume;
	InteractionVolume->InitSphereRadius(InteractionRadius);
	InteractionVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	InteractionVolume->SetCollisionObjectType(ECC_WorldDynamic);
	InteractionVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
	InteractionVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	InteractionVolume->SetGenerateOverlapEvents(true);

	PropVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PropVisual"));
	PropVisual->SetupAttachment(InteractionVolume);
	PropVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PropVisual->SetGenerateOverlapEvents(false);

	WorldLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("WorldLabel"));
	WorldLabel->SetupAttachment(InteractionVolume);
	WorldLabel->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
	WorldLabel->SetVerticalAlignment(EVerticalTextAligment::EVRTA_TextCenter);
	WorldLabel->SetWorldSize(WorldLabelSize);
}

void ACarnivalMissionInteractionActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bDoorAnimating)
	{
		return;
	}

	DoorAnimationAge += DeltaSeconds;
	const float Duration = FMath::Max(0.05f, DoorAnimationSeconds);
	const float Alpha = FMath::Clamp(DoorAnimationAge / Duration, 0.0f, 1.0f);
	const int32 Count = FMath::Min(ControlledDoorLeaves.Num(),
		FMath::Min(DoorAnimationStartRotations.Num(), DoorAnimationTargetRotations.Num()));
	for (int32 Index = 0; Index < Count; ++Index)
	{
		if (UStaticMeshComponent* Leaf = ControlledDoorLeaves[Index])
		{
			Leaf->SetRelativeRotation(FMath::Lerp(DoorAnimationStartRotations[Index], DoorAnimationTargetRotations[Index], Alpha));
		}
	}

	if (Alpha >= 1.0f)
	{
		bDoorAnimating = false;
		SetActorTickEnabled(false);
	}
}

void ACarnivalMissionInteractionActor::BeginPlay()
{
	Super::BeginPlay();
	InteractionVolume->SetSphereRadius(InteractionRadius);
	ApplyVisualSettings();
	CacheControlledDoorLeaves();
	if (UCarnivalMissionSubsystem* Mission = GetMissionSubsystem())
	{
		UpdateVisualAvailability(Mission);
		Mission->OnMissionChanged.AddDynamic(this, &ACarnivalMissionInteractionActor::HandleMissionStateChanged);
		ReceiveMissionStateChanged(Mission->GetMissionState(), Mission->GetCurrentObjective());
	}
	if (bTriggerOnOverlap)
	{
		InteractionVolume->OnComponentBeginOverlap.AddDynamic(this, &ACarnivalMissionInteractionActor::OnPlayerEnteredVolume);
	}
}

void ACarnivalMissionInteractionActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UCarnivalMissionSubsystem* Mission = GetMissionSubsystem())
	{
		Mission->OnMissionChanged.RemoveDynamic(this, &ACarnivalMissionInteractionActor::HandleMissionStateChanged);
	}
	Super::EndPlay(EndPlayReason);
}

void ACarnivalMissionInteractionActor::HandleMissionStateChanged(ECarnivalStoryMissionState NewState, FText Objective)
{
	if (NewState == ECarnivalStoryMissionState::FreePlay || NewState == ECarnivalStoryMissionState::FindMansion)
	{
		SetControlledDoorOpen(false, true);
	}
	UpdateVisualAvailability(GetMissionSubsystem());
	ReceiveMissionStateChanged(NewState, Objective);
}

bool ACarnivalMissionInteractionActor::RestoreSavedDoor(bool bOpen)
{
	if (Interaction != ECarnivalMissionInteraction::MusicRoomDoor) return false;
	if (ControlledDoorLeaves.IsEmpty()) CacheControlledDoorLeaves();
	return SetControlledDoorOpen(bOpen, true);
}

bool ACarnivalMissionInteractionActor::CanInteract(const ACarnivalPlayerCharacter* Player) const
{
	if (!Player || bTriggerOnOverlap || !IsActionAvailable(GetMissionSubsystem()))
	{
		return false;
	}

	const AActor* FocusTarget = InteractionTargetActor ? InteractionTargetActor.Get() : this;
	if (FVector::DistSquared(Player->GetActorLocation(), FocusTarget->GetActorLocation()) > FMath::Square(InteractionRadius))
	{
		return false;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	FHitResult Hit;
	FCollisionQueryParams Query(SCENE_QUERY_STAT(MissionInteractionFocus), false, Player);
	Query.AddIgnoredActor(this);
	Query.AddIgnoredActor(FocusTarget);
	if (Interaction == ECarnivalMissionInteraction::MusicRoomDoor && ControlledDoorActor)
	{
		// The closed leaf is the thing being interacted with, so it must not
		// hide its own nearby prompt from a player standing at the doorway.
		Query.AddIgnoredActor(ControlledDoorActor);
	}
	const FVector TraceStart = Player->GetActorLocation() + FVector(0.f, 0.f, 50.f);
	const FVector TraceEnd = FocusTarget->GetActorLocation() + FVector(0.f, 0.f, 40.f);
	return !World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Query);
}

FText ACarnivalMissionInteractionActor::GetPromptText() const
{
	if (!PromptOverride.IsEmpty())
	{
		return PromptOverride;
	}
	if (Interaction == ECarnivalMissionInteraction::CampaignStation)
	{
		for (const auto& Station : UCarnivalCampaignSubsystem::Stations()) if (Station.Id == CampaignStationId)
			return FText::FromString(CampaignAction == 0 ? TEXT("Inspect ") + Station.Location
				: FString::Printf(TEXT("Use %s control %d"), *Station.Location, CampaignAction));
		return FText::GetEmpty();
	}
	if (Interaction == ECarnivalMissionInteraction::MusicRoomDoor)
	{
		const UCarnivalMissionSubsystem* Mission = GetMissionSubsystem();
		return Mission && Mission->CanOpenMusicRoomDoor()
			? FText::FromString(TEXT("Open the music-room door"))
			: FText::FromString(TEXT("Locked - find the service key in the study"));
	}

	switch (Interaction)
	{
	case ECarnivalMissionInteraction::NoticeBoard: return FText::FromString(TEXT("Start the missing-worker investigation"));
	case ECarnivalMissionInteraction::MansionEntrance: return FText::FromString(TEXT("Enter the mansion on foot"));
	case ECarnivalMissionInteraction::FoyerGlove: return FText::FromString(TEXT("Inspect the wet work glove"));
	case ECarnivalMissionInteraction::StudyLogAndKey: return FText::FromString(TEXT("Read the log and take the service key"));
	case ECarnivalMissionInteraction::MusicRoomDoor: return FText::FromString(TEXT("Open the music-room door"));
	case ECarnivalMissionInteraction::Worker: return FText::FromString(TEXT("Talk to Eli"));
	case ECarnivalMissionInteraction::MusicBox: return FText::FromString(TEXT("Take the music box"));
	case ECarnivalMissionInteraction::MansionExit: return FText::FromString(TEXT("Leave the mansion"));
	case ECarnivalMissionInteraction::CarnivalReturn: return FText::FromString(TEXT("Return to the Carnival"));
	default: return FText::GetEmpty();
	}
}

bool ACarnivalMissionInteractionActor::TryInteract(ACarnivalPlayerCharacter* Player)
{
	if (!CanInteract(Player))
	{
		return false;
	}
	LastActionFailureMessage = FText::GetEmpty();
	if (!ExecuteMissionAction(Player))
	{
		const FText Reason = LastActionFailureMessage.IsEmpty() ? GetPromptText() : LastActionFailureMessage;
		if (UCarnivalMissionSubsystem* Mission = GetMissionSubsystem())
		{
			Mission->ShowPlayerFeedback(Reason);
		}
		ReceiveInteractionRejected(Player, Reason);
		return false;
	}

	if (!AcceptedFeedback.IsEmpty())
	{
		if (UCarnivalMissionSubsystem* Mission = GetMissionSubsystem())
		{
			Mission->ShowPlayerFeedback(AcceptedFeedback);
		}
	}

	ReceiveInteractionAccepted(Player);
	return true;
}

void ACarnivalMissionInteractionActor::OnPlayerEnteredVolume(UPrimitiveComponent*, AActor* OtherActor,
	UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (!bTriggerOnOverlap || !IsActionAvailable(GetMissionSubsystem()))
	{
		return;
	}

	if (ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(OtherActor))
	{
		if (ExecuteMissionAction(Player))
		{
			ReceiveInteractionAccepted(Player);
		}
	}
}

UCarnivalMissionSubsystem* ACarnivalMissionInteractionActor::GetMissionSubsystem() const
{
	UWorld* World = GetWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UCarnivalMissionSubsystem>() : nullptr;
}

bool ACarnivalMissionInteractionActor::IsActionAvailable(const UCarnivalMissionSubsystem* Mission) const
{
	if (Interaction == ECarnivalMissionInteraction::CampaignStation)
	{
		const auto* Campaign = GetGameInstance() ? GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>() : nullptr;
		return Campaign && Campaign->CanUseStation(CampaignStationId);
	}
	if (!Mission)
	{
		return false;
	}

	switch (Interaction)
	{
	case ECarnivalMissionInteraction::NoticeBoard:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::FreePlay || Mission->IsMissionComplete();
	case ECarnivalMissionInteraction::MansionEntrance:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::FindMansion;
	case ECarnivalMissionInteraction::FoyerGlove:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::SearchFoyer;
	case ECarnivalMissionInteraction::StudyLogAndKey:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::SearchStudy;
	case ECarnivalMissionInteraction::MusicRoomDoor:
		return !bControlledDoorOpen && (Mission->GetMissionState() == ECarnivalStoryMissionState::SearchFoyer
			|| Mission->GetMissionState() == ECarnivalStoryMissionState::SearchStudy
			|| Mission->GetMissionState() == ECarnivalStoryMissionState::FindWorker);
	case ECarnivalMissionInteraction::Worker:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::FindWorker;
	case ECarnivalMissionInteraction::MusicBox:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::RecoverMusicBox;
	case ECarnivalMissionInteraction::MansionExit:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::EscapeMansion;
	case ECarnivalMissionInteraction::CarnivalReturn:
		return Mission->GetMissionState() == ECarnivalStoryMissionState::ReturnToCarnival;
	default:
		return false;
	}
}

bool ACarnivalMissionInteractionActor::ExecuteMissionAction(ACarnivalPlayerCharacter* Player)
{
	if (Interaction == ECarnivalMissionInteraction::CampaignStation)
	{
		auto* Campaign = GetGameInstance() ? GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>() : nullptr;
		if (!Campaign) return false;
		const bool bAccepted = Campaign->UseStation(CampaignStationId, CampaignAction);
		LastActionFailureMessage = FText::FromString(Campaign->LastResult);
		if (auto* Mission = GetMissionSubsystem()) Mission->ShowPlayerFeedback(LastActionFailureMessage);
		return bAccepted;
	}
	UCarnivalMissionSubsystem* Mission = GetMissionSubsystem();
	if (!Mission || !IsActionAvailable(Mission))
	{
		return false;
	}
	if ((Interaction == ECarnivalMissionInteraction::MansionEntrance || Interaction == ECarnivalMissionInteraction::MansionExit)
		&& Player && (Player->MountedMotorcycle || Player->MountedBoat || Player->MountedHovercraft))
	{
		LastActionFailureMessage = FText::FromString(TEXT("Park outside and continue on foot."));
		return false;
	}

	switch (Interaction)
	{
	case ECarnivalMissionInteraction::NoticeBoard: return Mission->BeginStoryMission();
	case ECarnivalMissionInteraction::MansionEntrance: return Mission->ReportMansionArrival();
	case ECarnivalMissionInteraction::FoyerGlove: return Mission->CollectFoyerGlove();
	case ECarnivalMissionInteraction::StudyLogAndKey: return Mission->CollectStudyLogAndKey();
	case ECarnivalMissionInteraction::MusicRoomDoor:
		if (!Mission->CanOpenMusicRoomDoor())
		{
			LastActionFailureMessage = FText::FromString(TEXT("The music room is locked. Find the service key in the study."));
			return false;
		}
		// A streamed door can finish registering its components after this
		// persistent-level interaction actor begins play. Retry the cache when
		// the player uses the key instead of leaving a permanently dead link.
		if (ControlledDoorLeaves.IsEmpty())
		{
			CacheControlledDoorLeaves();
		}
		if (!SetControlledDoorOpen(true))
		{
			LastActionFailureMessage = FText::FromString(TEXT("The music-room door is not connected yet."));
			return false;
		}
		Mission->ShowPlayerFeedback(FText::FromString(TEXT("The service key turns. The music room opens.")));
		return true;
	case ECarnivalMissionInteraction::Worker: return Mission->ReportWorkerFound();
	case ECarnivalMissionInteraction::MusicBox:
		if (!Mission->RecoverMusicBox())
		{
			return false;
		}
		if (Player)
		{
			ACarnivalHauntedDoll* NearestMissionDoll = nullptr;
			float BestDistanceSquared = TNumericLimits<float>::Max();
			for (TActorIterator<ACarnivalHauntedDoll> It(GetWorld()); It; ++It)
			{
				if (!It->bMissionControlledInstance)
				{
					continue;
				}
				const float DistanceSquared = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
				if (DistanceSquared < BestDistanceSquared)
				{
					BestDistanceSquared = DistanceSquared;
					NearestMissionDoll = *It;
				}
			}
			if (!NearestMissionDoll || !NearestMissionDoll->BeginScriptedMissionScare(Player))
			{
				Mission->ShowPlayerFeedback(FText::FromString(TEXT("The music box is quiet. Leave by the foyer.")));
				Mission->ReportDollScareComplete();
			}
		}
		else
		{
			Mission->ShowPlayerFeedback(FText::FromString(TEXT("The music box is quiet. Leave by the foyer.")));
			Mission->ReportDollScareComplete();
		}
		return true;
	case ECarnivalMissionInteraction::MansionExit: return Mission->ReportMansionEscaped();
	case ECarnivalMissionInteraction::CarnivalReturn: return Mission->ReportCarnivalReturned();
	default: return false;
	}
}

void ACarnivalMissionInteractionActor::ApplyVisualSettings()
{
	if (!PropVisual)
	{
		return;
	}

	PropVisual->SetStaticMesh(InteractionMesh);
	PropVisual->SetRelativeLocation(InteractionMeshOffset);
	PropVisual->SetRelativeScale3D(InteractionMeshScale);
	PropVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WorldLabel->SetText(WorldLabelText);
	WorldLabel->SetRelativeLocation(WorldLabelOffset);
	WorldLabel->SetWorldSize(WorldLabelSize);
	WorldLabel->SetTextRenderColor(WorldLabelColor);
}

void ACarnivalMissionInteractionActor::ResolveControlledDoorActor()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	if (ControlledDoorActor && ControlledDoorActor->GetWorld() == World)
	{
		return;
	}

	// The door lives in a streamed map, so persist its identity rather than a
	// cross-level actor pointer. This also resolves the matching PIE duplicate.
	FName AuthoredName = ControlledDoorActorName;
	FVector AuthoredLocation = ControlledDoorActorLocation;
	if (ControlledDoorActor)
	{
		AuthoredName = ControlledDoorActor->GetFName();
		AuthoredLocation = ControlledDoorActor->GetActorLocation();
	}
	if (AuthoredName.IsNone())
	{
		return;
	}

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Candidate = *It;
		if (!Candidate || Candidate->GetFName() != AuthoredName
			|| FVector::DistSquared(Candidate->GetActorLocation(), AuthoredLocation) > FMath::Square(5.0f))
		{
			continue;
		}

		TArray<UStaticMeshComponent*> MeshComponents;
		Candidate->GetComponents<UStaticMeshComponent>(MeshComponents);
		bool bHasLeftLeaf = false;
		bool bHasRightLeaf = false;
		for (const UStaticMeshComponent* Component : MeshComponents)
		{
			if (!Component) continue;
			bHasLeftLeaf |= Component->GetName() == TEXT("SM_Door02_D");
			bHasRightLeaf |= Component->GetName() == TEXT("SM_Door02_E");
		}
		if (bHasLeftLeaf && bHasRightLeaf)
		{
			ControlledDoorActor = Candidate;
			return;
		}
	}
}

void ACarnivalMissionInteractionActor::UpdateVisualAvailability(const UCarnivalMissionSubsystem* Mission)
{
	if (!bHideVisualWhenConsumed || !Mission)
	{
		return;
	}

	bool bConsumed = false;
	switch (Interaction)
	{
	case ECarnivalMissionInteraction::FoyerGlove:
		bConsumed = Mission->bFoundFoyerGlove;
		break;
	case ECarnivalMissionInteraction::StudyLogAndKey:
		bConsumed = Mission->bHasServiceKey;
		break;
	case ECarnivalMissionInteraction::Worker:
		bConsumed = Mission->bFoundWorker;
		break;
	case ECarnivalMissionInteraction::MusicBox:
		bConsumed = Mission->bRecoveredMusicBox;
		break;
	default:
		break;
	}
	if (PropVisual) PropVisual->SetHiddenInGame(bConsumed);
	if (WorldLabel) WorldLabel->SetHiddenInGame(bConsumed);
}

void ACarnivalMissionInteractionActor::CacheControlledDoorLeaves()
{
	ResolveControlledDoorActor();
	ControlledDoorLeaves.Reset();
	ClosedDoorLeafRotations.Reset();
	DoorAnimationStartRotations.Reset();
	DoorAnimationTargetRotations.Reset();
	if (!ControlledDoorActor)
	{
		return;
	}

	TArray<UStaticMeshComponent*> MeshComponents;
	ControlledDoorActor->GetComponents<UStaticMeshComponent>(MeshComponents);
	for (UStaticMeshComponent* Component : MeshComponents)
	{
		if (!Component || (Component->GetName() != TEXT("SM_Door02_D") && Component->GetName() != TEXT("SM_Door02_E")))
		{
			continue;
		}
		ControlledDoorLeaves.Add(Component);
		ClosedDoorLeafRotations.Add(Component->GetRelativeRotation());
	}
}

bool ACarnivalMissionInteractionActor::SetControlledDoorOpen(bool bOpen, bool bSnap)
{
	if (bOpen == bControlledDoorOpen && !bDoorAnimating && !bSnap)
	{
		return ControlledDoorLeaves.Num() > 0;
	}
	if (ControlledDoorLeaves.IsEmpty() || ClosedDoorLeafRotations.Num() != ControlledDoorLeaves.Num())
	{
		return false;
	}

	bControlledDoorOpen = bOpen;
	DoorAnimationStartRotations.Reset();
	DoorAnimationTargetRotations.Reset();
	for (int32 Index = 0; Index < ControlledDoorLeaves.Num(); ++Index)
	{
		UStaticMeshComponent* Leaf = ControlledDoorLeaves[Index];
		if (!Leaf)
		{
			continue;
		}

		DoorAnimationStartRotations.Add(Leaf->GetRelativeRotation());
		FRotator Target = ClosedDoorLeafRotations[Index];
		if (bOpen)
		{
			const float Direction = Leaf->GetName() == TEXT("SM_Door02_D") ? 1.0f : -1.0f;
			Target.Yaw = FRotator::NormalizeAxis(Target.Yaw + Direction * DoorOpenAngleDegrees);
		}
		DoorAnimationTargetRotations.Add(Target);
	}

	if (bSnap)
	{
		for (int32 Index = 0; Index < ControlledDoorLeaves.Num() && Index < DoorAnimationTargetRotations.Num(); ++Index)
		{
			if (UStaticMeshComponent* Leaf = ControlledDoorLeaves[Index])
			{
				Leaf->SetRelativeRotation(DoorAnimationTargetRotations[Index]);
			}
		}
		bDoorAnimating = false;
		SetActorTickEnabled(false);
		return true;
	}

	DoorAnimationAge = 0.0f;
	bDoorAnimating = true;
	SetActorTickEnabled(true);
	return true;
}
