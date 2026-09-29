// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalWeaponBase.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "Engine/World.h"

ACarnivalWeaponBase::ACarnivalWeaponBase()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* RootComp = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(RootComp);

	WeaponStaticMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponStaticMesh"));
	WeaponStaticMesh->SetupAttachment(RootComp);
	WeaponStaticMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	WeaponSkeletalMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponSkeletalMesh"));
	WeaponSkeletalMesh->SetupAttachment(RootComp);
	WeaponSkeletalMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	WeaponType = ECarnivalWeaponType::Unarmed;
	HolsterSocketName = TEXT("weapon_holster_rSocket");
	EquipSocketName = TEXT("hand_rSocket");
	BaseDamage = 25.0f;
	AttackRange = 200.0f;
	FireRate = 0.5f;
}

void ACarnivalWeaponBase::BeginPlay()
{
	Super::BeginPlay();
}

void ACarnivalWeaponBase::AttachToCharacter(ACharacter* InCharacter, bool bEquipped)
{
	if (!InCharacter || !InCharacter->GetMesh())
	{
		return;
	}

	FName TargetSocket = bEquipped ? EquipSocketName : HolsterSocketName;
	SetOwner(InCharacter);
	SetInstigator(InCharacter);
	AttachToComponent(InCharacter->GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, TargetSocket);
}

void ACarnivalWeaponBase::PerformAttack(ACharacter* InstigatingCharacter)
{
	if (!IsValid(InstigatingCharacter) || !GetWorld() || AttackRange <= 0.f || BaseDamage <= 0.f
		|| GetWorld()->GetTimeSeconds() < NextAttackTime)
	{
		return;
	}
	NextAttackTime = GetWorld()->GetTimeSeconds() + FMath::Max(.01f, FireRate);
	LastHitActor = nullptr;
	LastDamageDealt = 0.f;

	FVector TraceStart;
	FRotator AimRotation;
	InstigatingCharacter->GetActorEyesViewPoint(TraceStart, AimRotation);
	const FVector Direction = AimRotation.Vector();
	const FVector TraceEnd = TraceStart + Direction * AttackRange;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalWeaponAttack), false, InstigatingCharacter);
	Params.AddIgnoredActor(this);
	APawn* Mount = Cast<APawn>(InstigatingCharacter->GetAttachParentActor());
	if (Mount) Params.AddIgnoredActor(Mount);
	TArray<AActor*> AttachedActors;
	InstigatingCharacter->GetAttachedActors(AttachedActors, true, true);
	Params.AddIgnoredActors(AttachedActors);
	FHitResult Hit;
	const bool bHit = WeaponType == ECarnivalWeaponType::Revolver
		? GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params)
		: GetWorld()->SweepSingleByChannel(Hit, TraceStart, TraceEnd, FQuat::Identity, ECC_Visibility,
			FCollisionShape::MakeSphere(FMath::Max(1.f, MeleeSweepRadius)), Params);
	if (bHit && IsValid(Hit.GetActor()))
	{
		LastHitActor = Hit.GetActor();
		AController* DamageController = InstigatingCharacter->GetController();
		if (!DamageController && Mount) DamageController = Mount->GetController();
		LastDamageDealt = UGameplayStatics::ApplyPointDamage(Hit.GetActor(), BaseDamage, Direction, Hit,
			DamageController, this, nullptr);
		if (ImpactEffect)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ImpactEffect, Hit.ImpactPoint, Hit.ImpactNormal.Rotation());
		}
	}

	if (AttackMontage && InstigatingCharacter->GetMesh() && InstigatingCharacter->GetMesh()->GetAnimInstance())
	{
		InstigatingCharacter->PlayAnimMontage(AttackMontage);
	}

	if (AttackSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, AttackSound, GetActorLocation());
	}
}
