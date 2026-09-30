#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalCrowdEditorLibrary.generated.h"

class UMetaHumanCharacter;
class UMetaHumanCollection;
class UMetaHumanCrowdAnimationConfig;
class UMetaHumanInstance;
class UMassEntityConfigAsset;
class UAnimSequence;
class USkeleton;
class UWorld;

UCLASS()
class CARNIVALPOPULATIONEDITOR_API UCarnivalCrowdEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static UMetaHumanCrowdAnimationConfig* CreateCrowdAnimationConfig(
        const FString& ObjectPath,
        UAnimSequence* IdleAnimation,
        UAnimSequence* WalkAnimation,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static UMetaHumanCollection* CreateCrowdCollectionForWardrobe(
        const FString& ObjectPath,
        USkeleton* TargetSkeleton,
        UMetaHumanCrowdAnimationConfig* AnimationConfig,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static UMetaHumanCollection* CreateAndBuildCrowdCollection(
        const FString& ObjectPath,
        const TArray<UMetaHumanCharacter*>& Characters,
        USkeleton* TargetSkeleton,
        UMetaHumanCrowdAnimationConfig* AnimationConfig,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static UMetaHumanInstance* CreateCrowdInstanceAsset(
        UMetaHumanCollection* Collection,
        UMetaHumanCharacter* Character,
        const FString& ObjectPath,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static AActor* PlaceInitializedMetaHumanActor(
        UMetaHumanInstance* Instance,
        const FString& ActorLabel,
        const FVector& Location,
        const FRotator& Rotation,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static UMassEntityConfigAsset* CreateMetaHumanMassEntityConfig(
        const FString& ObjectPath,
        const TArray<UMetaHumanInstance*>& CharacterInstances,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static AActor* PlaceMetaHumanMassSpawner(
        UMassEntityConfigAsset* EntityConfig,
        int32 Count,
        const FVector& Location,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static int32 CreateCrowdLoopZoneGraph(
        UWorld* World,
        const TArray<FVector>& Waypoints,
        float LaneWidth,
        FString& OutError);

    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static int32 CountBuiltZoneGraphLanes(UWorld* World);

    /** Read-only editor diagnostics; raw Mass counts include every entity type. */
    UFUNCTION(BlueprintCallable, Category = "Carnival|Crowd")
    static TArray<FString> DescribeLiveMassSimulation(UWorld* World);
};
