#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CarnivalDoorSubsystem.generated.h"

class UStaticMeshComponent;

/**
 * Makes the vendor BP_Door* props (hospital and mansion interiors) usable in play: the player's
 * context interact swings the nearest door's leaves open, away from the player, or back closed.
 * Leaves are the door's plate/leaf meshes; the closed pose is the frame's yaw. Doors driven by a
 * mission interaction (the music-room door) are left to that interaction. Doors tagged SealedDoorTag
 * (doorways that lead into walls or out of the demo) never open.
 */
UCLASS()
class CARNIVALGAME_API UCarnivalDoorSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static bool IsVendorDoor(const AActor* Actor);
	static bool IsSealed(const AActor* Door);

	/** Actor tag that keeps a vendor door permanently shut. */
	static const FName SealedDoorTag;

	/** Nearest usable vendor door whose leaves are within Reach of Location, or null. With bSealed, the nearest
	 *  sealed door instead (for a "Locked" prompt). */
	AActor* FindDoorNear(const FVector& Location, float Reach = 220.0f, bool bSealed = false) const;

	/** Opens a closed door (swinging away from From) or closes an open one. False if not a usable door. */
	bool ToggleDoor(AActor* Door, const FVector& From, bool bSnap = false);
	bool IsDoorOpen(AActor* Door);

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override { return Animating > 0; }

	static constexpr float OpenAngleDegrees = 90.0f;
	static constexpr float AnimationSeconds = 0.6f;

private:
	struct FLeaf
	{
		TWeakObjectPtr<UStaticMeshComponent> Component;
		float ClosedYaw = 0.0f;
		FRotator Start = FRotator::ZeroRotator;
		FRotator Target = FRotator::ZeroRotator;
	};
	struct FDoor
	{
		TArray<FLeaf> Leaves;
		bool bOpen = false;
		bool bAnimating = false;
		float Age = 0.0f;
	};

	FDoor* GetDoor(AActor* Door);
	bool IsMissionControlled(const AActor* Door) const;

	TMap<TWeakObjectPtr<AActor>, FDoor> Doors;
	int32 Animating = 0;
};
