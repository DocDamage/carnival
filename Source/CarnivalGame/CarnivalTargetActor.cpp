// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalTargetActor.h"
#include "CarnivalActivityBase.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "GameFramework/Controller.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Character.h"

namespace
{
ACarnivalPlayerCharacter* ResolveTargetPlayer(AActor* Actor)
{
	if (auto* Player = Cast<ACarnivalPlayerCharacter>(Actor)) return Player;
	if (auto* Bike = Cast<ACarnivalMotorcycle>(Actor)) return Bike->CurrentRider;
	if (auto* Boat = Cast<ACarnivalBoat>(Actor)) return Boat->CurrentRider;
	if (auto* Hover = Cast<ACarnivalHovercraft>(Actor)) return Hover->CurrentRider;
	return Actor ? Cast<ACarnivalPlayerCharacter>(Actor->GetInstigator()) : nullptr;
}

bool HasPlayerControl(const ACarnivalPlayerCharacter* Player)
{
	if (!IsValid(Player)) return false;
	if (Player->IsPlayerControlled()) return true;
	const APawn* Vehicle = Cast<APawn>(Player->GetAttachParentActor());
	if (!Vehicle || !Vehicle->IsPlayerControlled()) return false;
	if (const auto* Bike = Cast<ACarnivalMotorcycle>(Vehicle)) return Bike->CurrentRider == Player && Player->MountedMotorcycle == Bike;
	if (const auto* Boat = Cast<ACarnivalBoat>(Vehicle)) return Boat->CurrentRider == Player && Player->MountedBoat == Boat;
	if (const auto* Hover = Cast<ACarnivalHovercraft>(Vehicle)) return Hover->CurrentRider == Player && Player->MountedHovercraft == Hover;
	return false;
}
}

ACarnivalTargetActor::ACarnivalTargetActor()
{
	PrimaryActorTick.bCanEverTick = true;

	TargetMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TargetMesh"));
	RootComponent = TargetMesh;
	TargetMesh->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	TargetMesh->SetGenerateOverlapEvents(true);

	TriggerSphere = CreateDefaultSubobject<USphereComponent>(TEXT("TriggerSphere"));
	TriggerSphere->SetupAttachment(RootComponent);
	TriggerSphere->SetSphereRadius(120.0f);
	TriggerSphere->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	TriggerSphere->SetGenerateOverlapEvents(true);

	bIsHit = false;
	bIsRelicOrCollectible = false;
	PointValue = 100;
}

void ACarnivalTargetActor::BeginPlay()
{
	Super::BeginPlay();

	InitialLocation = GetActorLocation();
	InitialRotation = GetActorRotation();

	TriggerSphere->OnComponentBeginOverlap.AddDynamic(this, &ACarnivalTargetActor::OnOverlapBegin);
}

void ACarnivalTargetActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Gentle floating/rotating animation for relics and collectibles
	if (bIsRelicOrCollectible && !bIsHit)
	{
		AddActorLocalRotation(FRotator(0.0f, 45.0f * DeltaTime, 0.0f));
		const float BobOffset = FMath::Sin(GetWorld()->GetTimeSeconds() * 3.0f) * 8.0f;
		SetActorLocation(InitialLocation + FVector(0.0f, 0.0f, BobOffset));
	}
}

float ACarnivalTargetActor::TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, class AController* EventInstigator, AActor* DamageCauser)
{
	if (DamageAmount <= 0.f || bIsRelicOrCollectible || bIsHit) return 0.f;
	OnCollectedOrHit(EventInstigator ? EventInstigator->GetPawn() : DamageCauser);
	return bIsHit ? DamageAmount : 0.f;
}

void ACarnivalTargetActor::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bIsRelicOrCollectible && !bIsHit && Cast<ACarnivalPlayerCharacter>(OtherActor))
	{
		OnCollectedOrHit(OtherActor);
	}
}

void ACarnivalTargetActor::OnCollectedOrHit(AActor* InstigatorActor)
{
	ACarnivalPlayerCharacter* Player = ResolveTargetPlayer(InstigatorActor);
	if (bIsHit || !HasPlayerControl(Player)
		|| (IsValid(OwningActivity) && (OwningActivity->ActivityState != ECarnivalActivityState::Active
			|| OwningActivity->ActivePlayer != Player || !OwningActivity->Targets.Contains(this))))
	{
		return;
	}

	bIsHit = true;

	// Visual reaction: shrink or hide
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);

	if (OwningActivity)
	{
		OwningActivity->OnTargetHit(this);
	}
}

void ACarnivalTargetActor::ResetTarget()
{
	bIsHit = false;
	SetActorLocation(InitialLocation);
	SetActorRotation(InitialRotation);
	SetActorHiddenInGame(false);
	SetActorEnableCollision(true);
}
