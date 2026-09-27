#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalWorldEditorLibrary.generated.h"

/** Terrain authoring helpers used by the connected-world build scripts. */
UCLASS()
class CARNIVALPOPULATIONEDITOR_API UCarnivalWorldEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Carnival|World")
    static TArray<float> SampleLandscapeHeights(AActor* LandscapeActor, const TArray<FVector>& WorldPositions);

    /** Stamp a row-major height grid, blending its perimeter into the destination. */
    UFUNCTION(BlueprintCallable, Category="Carnival|World")
    static bool StampLandscapeHeightGrid(AActor* LandscapeActor, const FTransform& GridToWorld,
        int32 SizeX, int32 SizeY, float Spacing, const TArray<float>& Heights, float EdgeFalloff);

    /** Grade a land approach; bridge spans must be excluded from Points. */
    UFUNCTION(BlueprintCallable, Category="Carnival|World")
    static bool GradeLandscapeRoute(AActor* LandscapeActor, const TArray<FVector>& Points,
        float HalfWidth, float SideFalloff);

    UFUNCTION(BlueprintCallable, Category="Carnival|World")
    static AActor* CreateMeshInstances(UWorld* World, UStaticMesh* Mesh, const TArray<FTransform>& WorldTransforms,
        const FString& Label, bool EnableCollision);

    UFUNCTION(BlueprintCallable, Category="Carnival|World")
    static int32 ClearFoliageFromRoute(AActor* FoliageActor, const TArray<FVector>& Points, float Radius);
};
