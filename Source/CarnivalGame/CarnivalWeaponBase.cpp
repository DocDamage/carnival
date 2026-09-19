// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalWeaponBase.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"

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
	AttachToComponent(InCharacter->GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, TargetSocket);
}

void ACarnivalWeaponBase::PerformAttack(ACharacter* InstigatingCharacter)
{
	if (!InstigatingCharacter)
	{
		return;
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

