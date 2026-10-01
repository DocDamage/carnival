#include "CarnivalCrowdRoamTask.h"
#include "MassCommonFragments.h"
#include "MassEntityTemplateRegistry.h"
#include "MassMovementFragments.h"
#include "MassNavigationFragments.h"
#include "MassStateTreeDependency.h"
#include "MassStateTreeExecutionContext.h"
#include "MassZoneGraphNavigationFragments.h"
#include "MassZoneGraphNavigationUtils.h"
#include "StateTreeLinker.h"
#include "ZoneGraphSubsystem.h"
#include "Engine/World.h"

void UCarnivalCrowdNavigationPrerequisiteTrait::BuildTemplate(FMassEntityTemplateBuildContext& BuildContext, const UWorld&) const
{
	BuildContext.AddFragment<FAgentRadiusFragment>();
	BuildContext.AddFragment<FAgentHeightFragment>();
}

bool FCarnivalCrowdRoamTask::Link(FStateTreeLinker& Linker)
{
	Linker.LinkExternalData(LocationHandle);
	Linker.LinkExternalData(MoveTargetHandle);
	Linker.LinkExternalData(PathRequestHandle);
	Linker.LinkExternalData(ShortPathHandle);
	Linker.LinkExternalData(CachedLaneHandle);
	Linker.LinkExternalData(RadiusHandle);
	Linker.LinkExternalData(MovementHandle);
	Linker.LinkExternalData(ZoneGraphHandle);
	return true;
}

void FCarnivalCrowdRoamTask::GetDependencies(UE::MassBehavior::FStateTreeDependencyBuilder& Builder) const
{
	Builder.AddReadOnly(LocationHandle);
	Builder.AddReadWrite(MoveTargetHandle);
	Builder.AddReadWrite(PathRequestHandle);
	Builder.AddReadWrite(ShortPathHandle);
	Builder.AddReadWrite(CachedLaneHandle);
	Builder.AddReadOnly(RadiusHandle);
	Builder.AddReadOnly(MovementHandle);
	Builder.AddReadOnly(ZoneGraphHandle);
}

EStateTreeRunStatus FCarnivalCrowdRoamTask::EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult&) const
{
	const auto& Lane = Context.GetExternalData(LocationHandle);
	const auto& ZoneGraph = Context.GetExternalData(ZoneGraphHandle);
	auto& Data = Context.GetInstanceData(*this);
	if (!Lane.LaneHandle.IsValid() || Lane.LaneLength <= 1.f) return EStateTreeRunStatus::Failed;
	Data.Lane = Lane.LaneHandle;
	Data.NextLane.Reset();
	Data.bReverse = false;
	Data.TargetDistance = Lane.LaneLength;
	TArray<FZoneGraphLinkedLane> Outgoing;
	ZoneGraph.GetLinkedLanes(Lane.LaneHandle, EZoneLaneLinkType::Outgoing, EZoneLaneLinkFlags::All, EZoneLaneLinkFlags::None, Outgoing);
	Outgoing.RemoveAll([&](const FZoneGraphLinkedLane& Link)
	{
		FZoneGraphTagMask Tags;
		return !ZoneGraph.GetLaneTags(Link.DestLane, Tags) || !Tags.ContainsAny(FZoneGraphTagMask(1));
	});
	if (!Outgoing.IsEmpty())
	{
		const auto& MassContext = static_cast<const FMassStateTreeExecutionContext&>(Context);
		const uint32 Seed = HashCombineFast(GetTypeHash(MassContext.GetEntity().Index), GetTypeHash(Lane.LaneHandle.Index));
		Data.NextLane = Outgoing[Seed % Outgoing.Num()].DestLane;
	}
	else if (Lane.LaneLength - Lane.DistanceAlongLane < 100.f)
	{
		// A real dead-end is traversed back along the same lane; never teleport to another lane.
		Data.bReverse = true;
		Data.TargetDistance = 0.f;
	}
	return RequestPath(Context) ? EStateTreeRunStatus::Running : EStateTreeRunStatus::Failed;
}

bool FCarnivalCrowdRoamTask::RequestPath(FStateTreeExecutionContext& Context) const
{
	auto& MassContext = static_cast<FMassStateTreeExecutionContext&>(Context);
	const auto& Data = Context.GetInstanceData(*this);
	const auto& Lane = Context.GetExternalData(LocationHandle);
	if (Lane.LaneHandle != Data.Lane || !Context.GetWorld()) return false;
	auto& Request = Context.GetExternalData(PathRequestHandle).PathRequest;
	auto& MoveTarget = Context.GetExternalData(MoveTargetHandle);
	const auto& Movement = Context.GetExternalData(MovementHandle);
	Request = FZoneGraphShortPathRequest();
	Request.StartPosition = MoveTarget.Center;
	Request.TargetDistance = Data.TargetDistance;
	Request.bMoveReverse = Data.bReverse;
	Request.NextLaneHandle = Data.NextLane;
	Request.NextExitLinkType = Data.NextLane.IsValid() ? EZoneLaneLinkType::Outgoing : EZoneLaneLinkType::None;
	Request.EndOfPathIntent = EMassMovementAction::Stand;
	Request.AnticipationDistance.Set(50.f);
	const float Radius = Context.GetExternalData(RadiusHandle).Radius;
	const uint32 Seed = GetTypeHash(MassContext.GetEntity().Index);
	Request.EndOfPathOffset.Set((static_cast<float>(Seed % 101) / 50.f - 1.f) * Radius);
	const float Speed = FMath::Min(Movement.GenerateDesiredSpeed(FMassMovementStyleRef(), MassContext.GetEntity().Index), Movement.MaxSpeed);
	MoveTarget.CreateNewAction(EMassMovementAction::Move, *Context.GetWorld());
	return UE::MassNavigation::ActivateActionMove(*Context.GetWorld(), Context.GetOwner(), MassContext.GetEntity(),
		Context.GetExternalData(ZoneGraphHandle), Lane, Request, Radius, Speed, MoveTarget,
		Context.GetExternalData(ShortPathHandle), Context.GetExternalData(CachedLaneHandle));
}

EStateTreeRunStatus FCarnivalCrowdRoamTask::Tick(FStateTreeExecutionContext& Context, float) const
{
	const auto& Path = Context.GetExternalData(ShortPathHandle);
	if (!Path.IsDone()) return EStateTreeRunStatus::Running;
	if (Path.bPartialResult) return RequestPath(Context) ? EStateTreeRunStatus::Running : EStateTreeRunStatus::Failed;
	return EStateTreeRunStatus::Succeeded;
}
