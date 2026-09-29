#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalVehicleAuthoring.generated.h"

class USkeletalMesh;
class UPhysicsAsset;
class USkeletalMeshSocket;
class UBlueprint;

/** Small editor pipeline for saving collision on imported single-bone vehicle parts. */
UCLASS()
class CARNIVALGAME_API UCarnivalVehicleAuthoring : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Carnival|Vehicle Authoring", meta=(DevelopmentOnly))
    static UPhysicsAsset* CreateBodyCollision(USkeletalMesh* Mesh, const FString& PackagePath,
        float LowerHalfWidth = 0.f, float SplitHeight = 0.f);

    UFUNCTION(BlueprintCallable, Category="Carnival|Vehicle Authoring", meta=(DevelopmentOnly))
    static USkeletalMeshSocket* SetAttachmentSocket(USkeletalMesh* Mesh, FName SocketName,
        FName BoneName, FVector Location);

    UFUNCTION(BlueprintCallable, Category="Carnival|Vehicle Authoring", meta=(DevelopmentOnly))
    static int32 ConfigureMountedFootRig(UBlueprint* Blueprint);
};
