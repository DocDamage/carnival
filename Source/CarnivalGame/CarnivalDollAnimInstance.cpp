#include "CarnivalDollAnimInstance.h"
#include "CarnivalHauntedDoll.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/AnimSequence.h"
#include "AnimationRuntime.h"

struct FDollAnimProxy : public FAnimInstanceProxy
{
    explicit FDollAnimProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}
    FAnimNode_SequencePlayer_Standalone Current;
    FAnimNode_SequencePlayer_Standalone Previous;
    float Blend = 1.f;
    int32 Revision = INDEX_NONE;
    bool bChanged = false;

    virtual void Initialize(UAnimInstance* Instance) override
    {
        FAnimInstanceProxy::Initialize(Instance);
        Current.Initialize_AnyThread(FAnimationInitializeContext(this));
        Previous.Initialize_AnyThread(FAnimationInitializeContext(this));
    }
    virtual void PreUpdate(UAnimInstance* Instance, float DeltaSeconds) override
    {
        FAnimInstanceProxy::PreUpdate(Instance, DeltaSeconds);
        const ACarnivalHauntedDoll* Doll = Cast<ACarnivalHauntedDoll>(Instance->GetOwningActor());
        if (!Doll) return;
        bool Loop = true;
        float Rate = 1.f;
        UAnimSequence* Sequence = Doll->GetDesiredAnimation(Loop, Rate);
        if (Sequence != Current.GetSequence() || Revision != Doll->GetAnimationRevision())
        {
            Previous.SetSequence(Current.GetSequence());
            Previous.SetLoopAnimation(Current.IsLooping());
            Previous.SetPlayRate(Current.GetPlayRate());
            Previous.SetStartPosition(Current.GetAccumulatedTime());
            Previous.Initialize_AnyThread(FAnimationInitializeContext(this));
            Current.SetSequence(Sequence);
            Current.SetLoopAnimation(Loop);
            Current.SetStartPosition(0.f);
            Current.Initialize_AnyThread(FAnimationInitializeContext(this));
            Blend = Previous.GetSequence() ? 0.f : 1.f;
            Revision = Doll->GetAnimationRevision();
            bChanged = true;
        }
        Current.SetPlayRate(Rate);
        auto* DollInstance = CastChecked<UCarnivalDollAnimInstance>(Instance);
        DollInstance->CurrentAnimation = Sequence;
        DollInstance->PreviousAnimation = Blend < 1.f ? Cast<UAnimSequence>(Previous.GetSequence()) : nullptr;
        DollInstance->CurrentPlayRate = Rate;
        Blend = FMath::Min(1.f, Blend + DeltaSeconds / .12f);
    }
    virtual void CacheBones() override
    {
        Current.CacheBones_AnyThread(FAnimationCacheBonesContext(this));
        Previous.CacheBones_AnyThread(FAnimationCacheBonesContext(this));
    }
    virtual void UpdateAnimationNode(const FAnimationUpdateContext& Context) override
    {
        if (bChanged) { CacheBones(); bChanged = false; }
        Current.Update_AnyThread(Context.FractionalWeight(Blend));
        if (Blend < 1.f) Previous.Update_AnyThread(Context.FractionalWeight(1.f - Blend));
    }
    virtual bool Evaluate(FPoseContext& Output) override
    {
        Current.Evaluate_AnyThread(Output);
        if (Blend < 1.f && Previous.GetSequence())
        {
            FPoseContext OldPose(Output);
            Previous.Evaluate_AnyThread(OldPose);
            FAnimationPoseData Result(Output);
            const FAnimationPoseData OldData(OldPose);
            FAnimationRuntime::BlendTwoPosesTogetherInPlace(Result, OldData, Blend);
        }
        return true;
    }
};

UCarnivalDollAnimInstance::UCarnivalDollAnimInstance()
{
    RootMotionMode = ERootMotionMode::RootMotionFromEverything;
    bUseMultiThreadedAnimationUpdate = false;
}
FAnimInstanceProxy* UCarnivalDollAnimInstance::CreateAnimInstanceProxy() { return new FDollAnimProxy(this); }
void UCarnivalDollAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) { delete Proxy; }
