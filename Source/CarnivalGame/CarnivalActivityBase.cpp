// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalActivityBase.h"
#include "CarnivalTargetActor.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"

ACarnivalActivityBase::ACarnivalActivityBase()
{
	PrimaryActorTick.bCanEverTick = true;

	ActivityTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("ActivityTrigger"));
	RootComponent = ActivityTrigger;
	ActivityTrigger->SetBoxExtent(FVector(200.0f, 200.0f, 150.0f));
	ActivityTrigger->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	ActivityTrigger->SetGenerateOverlapEvents(true);

	PromptText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PromptText"));
	PromptText->SetupAttachment(RootComponent);
	PromptText->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));
	PromptText->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
	PromptText->SetWorldSize(14.0f);
	PromptText->SetText(FText::FromString(TEXT("Challenge")));
	PromptText->SetHiddenInGame(true);

	ActivityName = TEXT("Challenge");
	Description = TEXT("Complete the challenge before time runs out!");
	LocationName = TEXT("Carnival");
	ActivityType = ECarnivalChallengeType::StuntRally;
	ActivityState = ECarnivalActivityState::Inactive;

	TimeLimit = 60.0f;
	TimeRemaining = 60.0f;
	ElapsedTime = 0.0f;
	CurrentScore = 0;
	TargetScore = 500;

	GoldTime = 30.0f;
	SilverTime = 45.0f;
	BronzeTime = 60.0f;

	CurrentCheckpointIndex = 0;
	ActivePlayer = nullptr;
	bPlayerInTrigger = false;
}

void ACarnivalActivityBase::BeginPlay()
{
	Super::BeginPlay();

	ActivityTrigger->OnComponentBeginOverlap.AddDynamic(this, &ACarnivalActivityBase::OnTriggerOverlapBegin);
	ActivityTrigger->OnComponentEndOverlap.AddDynamic(this, &ACarnivalActivityBase::OnTriggerOverlapEnd);

	// Instructions and device/remapped controls belong in the contextual HUD.
	PromptText->SetWorldSize(14.0f);
	PromptText->SetText(FText::FromString(GetDisplayTitle()));
	UpdateWorldLabel();
	for (ACarnivalTargetActor* Target : Targets)
	{
		if (IsValid(Target)) Target->OwningActivity = this;
	}
}

void ACarnivalActivityBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	UpdateWorldLabel();

	if (ActivityState == ECarnivalActivityState::Active)
	{
		if (!IsValid(ActivePlayer))
		{
			AbortActivity();
			return;
		}
		ElapsedTime += FMath::Max(0.f, DeltaTime);
		TimeRemaining = FMath::Max(0.f, TimeLimit - ElapsedTime);

		if (Checkpoints.Num() > 0)
		{
			CheckPlayerCheckpoints();
		}

		if (ActivityState == ECarnivalActivityState::Active && TimeRemaining <= 0.0f)
		{
			CompleteActivity(false);
		}
	}
}

FString ACarnivalActivityBase::GetDisplayTitle() const
{
	FString Title = ActivityName.TrimStartAndEnd();
	if (!Title.RemoveFromStart(TEXT("Activity_"))) return Title.IsEmpty() ? TEXT("Challenge") : Title;
	FString Result;
	for (int32 Index = 0; Index < Title.Len(); ++Index)
	{
		const TCHAR Character = Title[Index];
		if (Character == TEXT('_'))
		{
			Result += TEXT(' ');
			continue;
		}
		if (Index > 0 && FChar::IsUpper(Character)
			&& (FChar::IsLower(Title[Index - 1]) || FChar::IsDigit(Title[Index - 1])
				|| (FChar::IsUpper(Title[Index - 1]) && Index + 1 < Title.Len() && FChar::IsLower(Title[Index + 1]))))
		{
			Result += TEXT(' ');
		}
		Result += Character;
	}
	return Result.IsEmpty() ? TEXT("Challenge") : Result;
}

void ACarnivalActivityBase::UpdateWorldLabel()
{
	APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0);
	const bool bNearby = Camera && FVector::DistSquared(Camera->GetCameraLocation(), GetActorLocation()) <= FMath::Square(1200.f);
	PromptText->SetHiddenInGame(!bNearby);
	if (bNearby)
	{
		// Face the local camera horizontally so the title cannot read backwards.
		const FVector Direction = Camera->GetCameraLocation() - PromptText->GetComponentLocation();
		PromptText->SetWorldRotation(FRotator(0.f, Direction.Rotation().Yaw, 0.f));
	}
}

void ACarnivalActivityBase::OnTriggerOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(OtherActor))
	{
		if (!Player->IsPlayerControlled()) return;
		bPlayerInTrigger = true;
		Player->NearbyActivity = this;
	}
}

void ACarnivalActivityBase::OnTriggerOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
	if (ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(OtherActor))
	{
		if (Player->NearbyActivity == this) Player->NearbyActivity = nullptr;
		if (Player->IsPlayerControlled()) bPlayerInTrigger = false;
	}
}

void ACarnivalActivityBase::StartActivity(ACarnivalPlayerCharacter* Player)
{
	if (!IsValid(Player) || ActivityState == ECarnivalActivityState::Active
		|| (IsValid(Player->ActiveActivity) && Player->ActiveActivity != this
			&& Player->ActiveActivity->ActivityState == ECarnivalActivityState::Active))
	{
		return;
	}

	ActivePlayer = Player;
	Player->ActiveActivity = this;
	ActivityState = ECarnivalActivityState::Active;
	ElapsedTime = 0.0f;
	TimeRemaining = TimeLimit;
	CurrentScore = 0;
	CurrentCheckpointIndex = 0;
	ScoredTargets.Reset();

	for (FCarnivalActivityCheckpoint& Cp : Checkpoints)
	{
		Cp.bReached = false;
	}

	for (ACarnivalTargetActor* Target : Targets)
	{
		if (IsValid(Target))
		{
			Target->OwningActivity = this;
			Target->ResetTarget();
		}
	}
}

void ACarnivalActivityBase::CheckPlayerCheckpoints()
{
	if (!ActivePlayer || !Checkpoints.IsValidIndex(CurrentCheckpointIndex))
	{
		return;
	}

	FVector PlayerLoc = ActivePlayer->GetActorLocation();
	const FCarnivalActivityCheckpoint& TargetCp = Checkpoints[CurrentCheckpointIndex];

	if (FVector::Dist(PlayerLoc, TargetCp.Location) <= TargetCp.Radius)
	{
		OnCheckpointReached(CurrentCheckpointIndex);
	}
}

void ACarnivalActivityBase::OnCheckpointReached(int32 CheckpointIndex)
{
	if (ActivityState == ECarnivalActivityState::Active && CheckpointIndex == CurrentCheckpointIndex
		&& Checkpoints.IsValidIndex(CheckpointIndex) && !Checkpoints[CheckpointIndex].bReached)
	{
		Checkpoints[CheckpointIndex].bReached = true;
		CurrentScore += 100;
		CurrentCheckpointIndex++;

		if (CurrentCheckpointIndex >= Checkpoints.Num())
		{
			CompleteActivity(true);
		}
	}
}

void ACarnivalActivityBase::OnTargetHit(ACarnivalTargetActor* Target)
{
	if (ActivityState != ECarnivalActivityState::Active || !IsValid(Target)
		|| !Targets.Contains(Target) || !Target->bIsHit || ScoredTargets.Contains(Target))
	{
		return;
	}

	ScoredTargets.Add(Target);
	CurrentScore += FMath::Max(0, Target->PointValue);

	// Check if all targets are hit
	bool bAllHit = true;
	for (ACarnivalTargetActor* T : Targets)
	{
		if (IsValid(T) && !ScoredTargets.Contains(T))
		{
			bAllHit = false;
			break;
		}
	}

	if (bAllHit && Targets.Num() > 0)
	{
		CompleteActivity(true);
	}
}

void ACarnivalActivityBase::CompleteActivity(bool bSuccess)
{
	if (ActivityState != ECarnivalActivityState::Active) return;
	ActivityState = bSuccess ? ECarnivalActivityState::Completed : ECarnivalActivityState::Failed;
}

void ACarnivalActivityBase::AbortActivity()
{
	ActivityState = ECarnivalActivityState::Inactive;
	ResetActivity();
}

void ACarnivalActivityBase::ResetActivity()
{
	if (IsValid(ActivePlayer) && ActivePlayer->ActiveActivity == this) ActivePlayer->ActiveActivity = nullptr;
	ActivePlayer = nullptr;
	ScoredTargets.Reset();
	ActivityState = ECarnivalActivityState::Inactive;
	ElapsedTime = 0.0f;
	TimeRemaining = TimeLimit;
	CurrentScore = 0;
	CurrentCheckpointIndex = 0;

	for (FCarnivalActivityCheckpoint& Cp : Checkpoints)
	{
		Cp.bReached = false;
	}

	for (ACarnivalTargetActor* Target : Targets)
	{
		if (IsValid(Target))
		{
			Target->ResetTarget();
		}
	}
}

FString ACarnivalActivityBase::GetCurrentObjectiveText() const
{
	if (Checkpoints.Num() > 0 && Checkpoints.IsValidIndex(CurrentCheckpointIndex))
	{
		return FString::Printf(TEXT("Checkpoint %d/%d: %s"), CurrentCheckpointIndex + 1, Checkpoints.Num(), *Checkpoints[CurrentCheckpointIndex].Description);
	}
	else if (Targets.Num() > 0)
	{
		int32 HitCount = 0;
		for (ACarnivalTargetActor* T : Targets)
		{
			if (T && T->bIsHit)
			{
				HitCount++;
			}
		}
		return FString::Printf(TEXT("Targets: %d/%d | Score: %d/%d"), HitCount, Targets.Num(), CurrentScore, TargetScore);
	}

	return Description;
}

FString ACarnivalActivityBase::GetMedalRating() const
{
	if (ActivityState != ECarnivalActivityState::Completed) return TEXT("");
	if (ElapsedTime <= GoldTime)
	{
		return TEXT("GOLD MEDAL");
	}
	else if (ElapsedTime <= SilverTime)
	{
		return TEXT("SILVER MEDAL");
	}
	else if (ElapsedTime <= BronzeTime)
	{
		return TEXT("BRONZE MEDAL");
	}

	return TEXT("COMPLETED");
}
