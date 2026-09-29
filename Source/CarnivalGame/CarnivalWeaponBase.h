// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalWeaponBase.generated.h"

class UStaticMeshComponent;
class USkeletalMeshComponent;
class UAnimMontage;
class USoundBase;
class UNiagaraSystem;

UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalWeaponBase : public AActor
{
	GENERATED_BODY()

public:
	ACarnivalWeaponBase();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* WeaponStaticMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USkeletalMeshComponent* WeaponSkeletalMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	ECarnivalWeaponType WeaponType;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FName HolsterSocketName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FName EquipSocketName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float BaseDamage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float AttackRange;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float FireRate;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0"))
	float MeleeSweepRadius = 25.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<AActor> LastHitActor;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Feedback")
	float LastDamageDealt = 0.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Effects")
	USoundBase* AttackSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Effects")
	UNiagaraSystem* ImpactEffect;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Animation")
	UAnimMontage* AttackMontage;

	UFUNCTION(BlueprintCallable, Category = "Weapon")
	virtual void AttachToCharacter(ACharacter* InCharacter, bool bEquipped);

	UFUNCTION(BlueprintCallable, Category = "Weapon")
	virtual void PerformAttack(ACharacter* InstigatingCharacter);

protected:
	virtual void BeginPlay() override;

	double NextAttackTime = 0.0;
};
