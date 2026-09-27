#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalHauntedDoll.generated.h"

class UAnimSequence;
class USoundBase;
class USoundAttenuation;

UENUM(BlueprintType)
enum class EDollEncounterState : uint8
{
    Idle, Notice, Approach, Chase, Scare, Cooldown, Returning
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FDollScareEvent, APawn*, Player);

/** A reusable, local-player horror encounter with a bounded chase and reset. */
UCLASS(Blueprintable)
class CARNIVALGAME_API ACarnivalHauntedDoll : public ACharacter
{
    GENERATED_BODY()
public:
    ACarnivalHauntedDoll();
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Detection") bool bEncounterEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Detection", meta=(ClampMin="0")) float DetectionDistance = 850.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Detection", meta=(ClampMin="0", ClampMax="180")) float DetectionHalfAngle = 70.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Detection", meta=(ClampMin="0")) float LoseSightSeconds = 2.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Movement", meta=(ClampMin="0")) float WalkSpeed = 27.21774f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Movement", meta=(ClampMin="0")) float RunSpeed = 101.19048f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Movement", meta=(ClampMin="0")) float ChaseAfterSeconds = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Movement", meta=(ClampMin="0")) float LeashDistance = 1500.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Scare", meta=(ClampMin="50")) float ScareDistance = 130.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Scare", meta=(ClampMin="0")) float CooldownSeconds = 8.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Scare", meta=(ClampMin="0", ClampMax="1")) float ScareVolume = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Scare") TObjectPtr<USoundBase> ScareSound;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Scare") TObjectPtr<USoundAttenuation> ScareAttenuation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> WalkAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> RunAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> NoticeAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> ScareAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> ReachAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> JumpAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Doll|Animations") TObjectPtr<UAnimSequence> RamsterIdleAnimation;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll|Status") EDollEncounterState EncounterState = EDollEncounterState::Idle;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll|Status") TObjectPtr<APawn> TargetPlayer;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll|Status") int32 ScareCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Doll|Status") FVector HomeLocation;
    UPROPERTY(BlueprintAssignable, Category="Doll|Scare") FDollScareEvent OnScare;

    /** Optional trigger-volume entry point. Still requires an unobstructed nearby pawn. */
    UFUNCTION(BlueprintCallable, Category="Doll") bool ActivateForPlayer(APawn* Player);
    UFUNCTION(BlueprintPure, Category="Doll") bool CanDetectPawn(const APawn* Player) const;
    UFUNCTION(BlueprintCallable, Category="Doll") void ResetEncounter();
    /** Preview extra same-skeleton actions without enabling a chase. */
    UFUNCTION(BlueprintCallable, Category="Doll") bool PlayDollAction(UAnimSequence* Animation);

    UAnimSequence* GetDesiredAnimation(bool& bLooping, float& PlayRate) const;
    int32 GetAnimationRevision() const { return AnimationRevision; }

protected:
    virtual void BeginPlay() override;
private:
    void SetEncounterState(EDollEncounterState State);
    void MoveToward(const FVector& Destination, float Speed, float DeltaSeconds);
    void StopDollMovement();
    void FacePoint(const FVector& Point, float DeltaSeconds);
    bool HasSightTo(const APawn* Player) const;
    float StateAge = 0.f;
    float LostSightAge = 0.f;
    float SenseAge = 0.f;
    float MoveRequestAge = 0.f;
    float StuckAge = 0.f;
    float ActionAge = 0.f;
    int32 AnimationRevision = 0;
    FRotator HomeRotation;
    FVector LastProgressLocation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> ManualAction;
};
