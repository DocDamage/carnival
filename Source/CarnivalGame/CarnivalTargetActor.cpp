// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalTargetActor.h"
#include "CarnivalActivityBase.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Character.h"

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
		float BobOffset = FMath::Sin(GetWorld()->GetTimeSeconds() * 3.0f) * 0.4f;
		AddActorWorldOffset(FVector(0.0f, 0.0f, BobOffset));
	}
}

float ACarnivalTargetActor::TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, class AController* EventInstigator, AActor* DamageCauser)
{
	OnCollectedOrHit(DamageCauser);
	return DamageAmount;
}

void ACarnivalTargetActor::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bIsRelicOrCollectible && !bIsHit && Cast<ACharacter>(OtherActor))
	{
		OnCollectedOrHit(OtherActor);
	}
}

void ACarnivalTargetActor::OnCollectedOrHit(AActor* InstigatorActor)
{
	if (bIsHit)
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

