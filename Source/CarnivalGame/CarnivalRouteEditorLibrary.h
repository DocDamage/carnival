#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalRouteEditorLibrary.generated.h"

class USkeletalMesh;
class UPhysicsAsset;
class UMaterial;
class UBlueprint;

/** Local authoring helpers; no changes are performed during gameplay. */
UCLASS()
class CARNIVALGAME_API UCarnivalRouteEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Read-only provenance for a constructed ride's seat components and SCS. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static TArray<FString> DescribeRideSeatConstruction(AActor* Ride);

    /** Remove one measured legacy SCS duplicate from a project Ferris Blueprint. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static int32 RepairDuplicateFerrisSeatBlueprint(UBlueprint* Blueprint);

    /** Paint a visibility hole in a bounded world XY rectangle of a copied landscape. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor")
    static bool CutLandscapeOpening(AActor* LandscapeActor, FVector WorldMinimum, FVector WorldMaximum, FTransform LevelTransform);

    /** Create a kinematic attachment body without filling the gaps between sails. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static UPhysicsAsset* CreateSailAnchorCollision(USkeletalMesh* Mesh, const FString& PackagePath);

    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static bool AddLandscapeVisibilityMask(UMaterial* CopiedMaterial);

    /** Remove the foliage instances of one InstancedFoliageActor whose world location lies in a small box (at most
     *  20 x 20 m) and whose foliage-type mesh name contains MeshNameContains, through the foliage system's own
     *  bookkeeping. Returns the number removed, or -1 if the arguments are refused. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static int32 RemoveFoliageInBox(AActor* FoliageActor, FVector WorldMinimum, FVector WorldMaximum, const FString& MeshNameContains);

    /** Read-only: for one InstancedFoliageActor, each foliage record (type, source, owned component, instances in the
     *  box) and each instanced mesh component with instances in the box, marked when no foliage record owns it. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Editor", meta=(DevelopmentOnly))
    static TArray<FString> DescribeFoliageInBox(AActor* FoliageActor, FVector WorldMinimum, FVector WorldMaximum);
};
