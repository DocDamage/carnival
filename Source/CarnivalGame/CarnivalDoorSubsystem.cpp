#include "CarnivalDoorSubsystem.h"
#include "CarnivalMissionInteractionActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"

namespace
{
	bool IsLeafMesh(const UStaticMeshComponent* Component)
	{
		const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
		if (!Mesh) return false;
		const FString Name = Mesh->GetName();
		return Name.Contains(TEXT("Door_Plate")) || Name == TEXT("SM_Door02_D") || Name == TEXT("SM_Door02_E");
	}

	bool IsFrameMesh(const UStaticMeshComponent* Component)
	{
		const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
		return Mesh && (Mesh->GetName().Contains(TEXT("Door_Frame")) || Mesh->GetName().Contains(TEXT("DoorStep")));
	}

	/** World-space centre of the leaf's mesh bounds if the leaf had relative rotation Rotation. */
	FVector LeafCentreAt(const UStaticMeshComponent* Leaf, const FRotator& Rotation)
	{
		const FTransform Relative(Rotation, Leaf->GetRelativeLocation(), Leaf->GetRelativeScale3D());
		const FTransform Parent = Leaf->GetAttachParent() ? Leaf->GetAttachParent()->GetComponentTransform() : FTransform::Identity;
		const FVector LocalCentre = Leaf->GetStaticMesh() ? Leaf->GetStaticMesh()->GetBounds().Origin : FVector::ZeroVector;
		return (Relative * Parent).TransformPosition(LocalCentre);
	}
}

const FName UCarnivalDoorSubsystem::SealedDoorTag(TEXT("CarnivalSealedDoor"));

bool UCarnivalDoorSubsystem::IsVendorDoor(const AActor* Actor)
{
	return Actor && Actor->GetClass()->GetName().StartsWith(TEXT("BP_Door"));
}

bool UCarnivalDoorSubsystem::IsSealed(const AActor* Door)
{
	return Door && Door->ActorHasTag(SealedDoorTag);
}

bool UCarnivalDoorSubsystem::IsMissionControlled(const AActor* Door) const
{
	for (TActorIterator<ACarnivalMissionInteractionActor> It(GetWorld()); It; ++It)
	{
		if (It->Interaction != ECarnivalMissionInteraction::MusicRoomDoor) continue;
		if (It->ControlledDoorActor == Door) return true;
		if (!It->ControlledDoorActorName.IsNone() && It->ControlledDoorActorName == Door->GetFName()
			&& (It->ControlledDoorActorLocation.IsNearlyZero() || FVector::Dist(It->ControlledDoorActorLocation, Door->GetActorLocation()) < 300.0f)) return true;
	}
	return false;
}

UCarnivalDoorSubsystem::FDoor* UCarnivalDoorSubsystem::GetDoor(AActor* Door)
{
	if (!IsVendorDoor(Door) || Door->GetWorld() != GetWorld()) return nullptr;
	if (FDoor* Existing = Doors.Find(Door)) return Existing->Leaves.IsEmpty() ? nullptr : Existing;

	FDoor& State = Doors.Add(Door);
	if (IsMissionControlled(Door) || IsSealed(Door)) return nullptr;
	TArray<UStaticMeshComponent*> Meshes;
	Door->GetComponents<UStaticMeshComponent>(Meshes);
	float FrameYaw = 0.0f;
	for (const UStaticMeshComponent* Mesh : Meshes)
	{
		if (IsFrameMesh(Mesh)) { FrameYaw = Mesh->GetRelativeRotation().Yaw; break; }
	}
	// Only a door with every leaf swung out counts as open. Vendor double doors are often authored with one leaf
	// ajar; treating those as open made the first interact slam them shut in the player's face.
	bool bAllLeavesOpen = true;
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (!IsLeafMesh(Mesh)) continue;
		FLeaf Leaf;
		Leaf.Component = Mesh;
		Leaf.ClosedYaw = FrameYaw;
		State.Leaves.Add(Leaf);
		if (FMath::Abs(FRotator::NormalizeAxis(Mesh->GetRelativeRotation().Yaw - FrameYaw)) <= 20.0f) bAllLeavesOpen = false;
	}
	State.bOpen = bAllLeavesOpen && !State.Leaves.IsEmpty();
	return State.Leaves.IsEmpty() ? nullptr : &State;
}

bool UCarnivalDoorSubsystem::IsDoorOpen(AActor* Door)
{
	const FDoor* State = GetDoor(Door);
	return State && State->bOpen;
}

AActor* UCarnivalDoorSubsystem::FindDoorNear(const FVector& Location, float Reach) const
{
	AActor* Best = nullptr;
	float BestDistance = Reach;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Actor = *It;
		if (!IsVendorDoor(Actor) || IsSealed(Actor) || FVector::DistSquared(Actor->GetActorLocation(), Location) > FMath::Square(Reach + 400.0f)) continue;
		if (const FDoor* Known = Doors.Find(Actor); Known && Known->Leaves.IsEmpty()) continue;
		TArray<UStaticMeshComponent*> Meshes;
		Actor->GetComponents<UStaticMeshComponent>(Meshes);
		for (const UStaticMeshComponent* Mesh : Meshes)
		{
			if (!IsLeafMesh(Mesh)) continue;
			const float Distance = FMath::Sqrt(Mesh->Bounds.GetBox().ComputeSquaredDistanceToPoint(Location));
			if (Distance < BestDistance && !IsMissionControlled(Actor))
			{
				BestDistance = Distance;
				Best = Actor;
			}
		}
	}
	return Best;
}

bool UCarnivalDoorSubsystem::ToggleDoor(AActor* Door, const FVector& From, bool bSnap)
{
	FDoor* State = GetDoor(Door);
	if (!State) return false;
	if (State->bAnimating) --Animating;
	State->bOpen = !State->bOpen;
	for (FLeaf& Leaf : State->Leaves)
	{
		UStaticMeshComponent* Component = Leaf.Component.Get();
		if (!Component) continue;
		// Vendor leaves are authored Static; they must be Movable to swing at runtime.
		if (Component->Mobility != EComponentMobility::Movable) Component->SetMobility(EComponentMobility::Movable);
		Leaf.Start = Component->GetRelativeRotation();
		Leaf.Target = Leaf.Start;
		Leaf.Target.Yaw = Leaf.ClosedYaw;
		if (State->bOpen)
		{
			// Swing whichever way carries the leaf away from the player.
			FRotator Plus = Leaf.Target, Minus = Leaf.Target;
			Plus.Yaw += OpenAngleDegrees;
			Minus.Yaw -= OpenAngleDegrees;
			const float PlusDistance = FVector::Dist2D(LeafCentreAt(Component, Plus), From);
			const float MinusDistance = FVector::Dist2D(LeafCentreAt(Component, Minus), From);
			Leaf.Target = PlusDistance >= MinusDistance ? Plus : Minus;
		}
		// Take the short way round from the current yaw.
		Leaf.Target.Yaw = Leaf.Start.Yaw + FRotator::NormalizeAxis(Leaf.Target.Yaw - Leaf.Start.Yaw);
		if (bSnap) Component->SetRelativeRotation(Leaf.Target);
	}
	State->bAnimating = !bSnap;
	State->Age = 0.0f;
	if (State->bAnimating) ++Animating;
	return true;
}

void UCarnivalDoorSubsystem::Tick(float DeltaTime)
{
	for (auto& Pair : Doors)
	{
		FDoor& State = Pair.Value;
		if (!State.bAnimating) continue;
		State.Age += DeltaTime;
		const float Alpha = FMath::Clamp(State.Age / AnimationSeconds, 0.0f, 1.0f);
		const float Eased = FMath::InterpEaseInOut(0.0f, 1.0f, Alpha, 2.0f);
		for (const FLeaf& Leaf : State.Leaves)
		{
			if (UStaticMeshComponent* Component = Leaf.Component.Get())
			{
				Component->SetRelativeRotation(FMath::Lerp(Leaf.Start, Leaf.Target, Eased));
			}
		}
		if (Alpha >= 1.0f)
		{
			State.bAnimating = false;
			--Animating;
		}
	}
}

TStatId UCarnivalDoorSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCarnivalDoorSubsystem, STATGROUP_Tickables);
}
