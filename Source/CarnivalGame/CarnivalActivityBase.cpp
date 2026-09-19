// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalActivityBase.h"
#include "CarnivalTargetActor.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Kismet/GameplayStatics.h"

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
	PromptText->SetWorldSize(32.0f);
	PromptText->SetText(FText::FromString(TEXT("ACTIVITY TRIGGER")));

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

	FString DisplayStr = FString::Printf(TEXT("[E] START: %s\n%s"), *ActivityName, *Description);
	PromptText->SetText(FText::FromString(DisplayStr));
}

void ACarnivalActivityBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (ActivityState == ECarnivalActivityState::Active)
	{
		ElapsedTime += DeltaTime;
		TimeRemaining -= DeltaTime;

		if (Checkpoints.Num() > 0)
		{
			CheckPlayerCheckpoints();
		}

		if (TimeRemaining <= 0.0f)
		{
			CompleteActivity(false);
		}
	}
}

void ACarnivalActivityBase::OnTriggerOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (ACarnivalPlayerCharacter* Player = Cast<ACarnivalPlayerCharacter>(OtherActor))
	{
		bPlayerInTrigger = true;
		ActivePlayer = Player;
	}
}

void ACarnivalActivityBase::OnTriggerOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
	if (OtherActor == ActivePlayer)
	{
		bPlayerInTrigger = false;
	}
}

void ACarnivalActivityBase::StartActivity(ACarnivalPlayerCharacter* Player)
{
	if (!Player)
	{
		return;
	}

	ActivePlayer = Player;
	ActivityState = ECarnivalActivityState::Active;
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
		if (Target)
		{
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
	if (Checkpoints.IsValidIndex(CheckpointIndex))
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
	if (!Target)
	{
		return;
	}

	CurrentScore += Target->PointValue;

	// Check if all targets are hit
	bool bAllHit = true;
	for (ACarnivalTargetActor* T : Targets)
	{
		if (T && !T->bIsHit)
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
	ActivityState = bSuccess ? ECarnivalActivityState::Completed : ECarnivalActivityState::Failed;
}

void ACarnivalActivityBase::AbortActivity()
{
	ActivityState = ECarnivalActivityState::Inactive;
	ResetActivity();
}

void ACarnivalActivityBase::ResetActivity()
{
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
		if (Target)
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
