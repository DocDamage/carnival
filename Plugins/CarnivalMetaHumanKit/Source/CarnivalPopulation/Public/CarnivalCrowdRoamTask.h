#pragma once

#include "MassStateTreeTypes.h"
#include "MassEntityTraitBase.h"
#include "ZoneGraphTypes.h"
#include "CarnivalCrowdRoamTask.generated.h"

struct FMassZoneGraphLaneLocationFragment;
struct FMassMoveTargetFragment;
struct FMassZoneGraphShortPathFragment;
struct FMassZoneGraphCachedLaneFragment;
struct FMassZoneGraphPathRequestFragment;
struct FAgentRadiusFragment;
struct FMassMovementParameters;
class UZoneGraphSubsystem;

USTRUCT()
struct FCarnivalCrowdRoamInstanceData
{
	GENERATED_BODY()
	UPROPERTY() FZoneGraphLaneHandle Lane;
	UPROPERTY() FZoneGraphLaneHandle NextLane;
	UPROPERTY() float TargetDistance = 0.f;
	UPROPERTY() bool bReverse = false;
};

/** Requests ordinary Mass lane paths. Steering, avoidance and movement remain engine-owned. */
USTRUCT(meta=(DisplayName="Carnival Guest Roam"))
struct CARNIVALPOPULATION_API FCarnivalCrowdRoamTask : public FMassStateTreeTaskBase
{
	GENERATED_BODY()
	using FInstanceDataType = FCarnivalCrowdRoamInstanceData;
protected:
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }
	virtual bool Link(FStateTreeLinker& Linker) override;
	virtual void GetDependencies(UE::MassBehavior::FStateTreeDependencyBuilder& Builder) const override;
	virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
	virtual EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context, float DeltaTime) const override;
private:
	bool RequestPath(FStateTreeExecutionContext& Context) const;
	TStateTreeExternalDataHandle<FMassZoneGraphLaneLocationFragment> LocationHandle;
	TStateTreeExternalDataHandle<FMassMoveTargetFragment> MoveTargetHandle;
	TStateTreeExternalDataHandle<FMassZoneGraphPathRequestFragment> PathRequestHandle;
	TStateTreeExternalDataHandle<FMassZoneGraphShortPathFragment> ShortPathHandle;
	TStateTreeExternalDataHandle<FMassZoneGraphCachedLaneFragment> CachedLaneHandle;
	TStateTreeExternalDataHandle<FAgentRadiusFragment> RadiusHandle;
	TStateTreeExternalDataHandle<FMassMovementParameters> MovementHandle;
	TStateTreeExternalDataHandle<UZoneGraphSubsystem> ZoneGraphHandle;
};

/** Navigation dimensions are independent of representation distance/quality. */
UCLASS()
class CARNIVALPOPULATION_API UCarnivalCrowdNavigationPrerequisiteTrait : public UMassEntityTraitBase
{
	GENERATED_BODY()
public:
	virtual void BuildTemplate(FMassEntityTemplateBuildContext& BuildContext, const UWorld& World) const override;
};
