#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "CarnivalDollAnimInstance.generated.h"

/** Native animation controller: same-skeleton clips, short blends and root motion. */
UCLASS(Transient, Blueprintable)
class CARNIVALGAME_API UCarnivalDollAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UCarnivalDollAnimInstance();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll") TObjectPtr<UAnimSequence> CurrentAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> PreviousAnimation;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll") float CurrentPlayRate = 1.f;
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
};
