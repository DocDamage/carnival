#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PhysicsVolume.h"
#include "CarnivalWaterVolume.generated.h"

class UBoxComponent;

/**
 * Box-shaped swimming water. Unlike a brush volume it is sized by WaterExtent, so it can be placed and resized
 * from scripts; the box is built into the brush collision, so character swimming, surface floating and leaving
 * the water all use the engine's standard water-volume behaviour. The surface is the top of the box.
 * Flooded interiors set bSolidSurface so swimmers cannot rise out of the water into open space above it.
 */
UCLASS()
class CARNIVALGAME_API ACarnivalWaterVolume : public APhysicsVolume
{
	GENERATED_BODY()

public:
	ACarnivalWaterVolume(const FObjectInitializer& ObjectInitializer);

	/** Half size of the water box, in the actor's local space. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Water", meta = (ClampMin = "10.0"))
	FVector WaterExtent = FVector(1000.f, 1000.f, 500.f);

	/** Adds a blocking lid at the surface (for flooded interiors with nothing above the water). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Water")
	bool bSolidSurface = false;

	/** Fog density of the underwater look, per metre of view distance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Water|Look", meta = (ClampMin = "0.0"))
	float UnderwaterFogPerMetre = 0.08f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Water|Look")
	FLinearColor UnderwaterFogColor = FLinearColor(0.012f, 0.075f, 0.095f);

	UPROPERTY(VisibleAnywhere, Category = "Water")
	TObjectPtr<UBoxComponent> SurfaceLid;

	float GetSurfaceZ() const;
	bool ContainsPoint(const FVector& Point) const;

	/** Highest-priority water volume containing Point, or null. */
	static ACarnivalWaterVolume* FindAt(const UWorld* World, const FVector& Point);

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void PostInitializeComponents() override;
	virtual bool IsOverlapInVolume(const USceneComponent& TestComponent) const override;

	void RebuildShape();
};
