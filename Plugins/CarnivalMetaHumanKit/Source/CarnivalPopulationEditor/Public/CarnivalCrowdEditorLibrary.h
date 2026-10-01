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
class UStateTree;
class UBlueprint;
class UMaterialFunctionInterface;

USTRUCT(BlueprintType)
struct FCarnivalCrowdEntitySample
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) int32 EntityIndex = 0;
    UPROPERTY(BlueprintReadOnly) int32 EntitySerial = 0;
    UPROPERTY(BlueprintReadOnly) FString AppearanceSource;
    UPROPERTY(BlueprintReadOnly) int32 RepresentationType = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) FVector Location = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) FVector Velocity = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) int32 LaneIndex = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) float LaneDistance = 0.f;
    UPROPERTY(BlueprintReadOnly) bool bBehaviorActive = false;
    UPROPERTY(BlueprintReadOnly) float AgentRadius = 0.f;
    UPROPERTY(BlueprintReadOnly) bool bInAvoidanceGrid = false;
    UPROPERTY(BlueprintReadOnly) int32 MovementAction = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) bool bSteeringFallingBehind = false;
};

UCLASS()
class CARNIVALPOPULATIONEDITOR_API UCarnivalCrowdEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static UStateTree* ConfigureCrowdRoaming(UMassEntityConfigAsset* Config, const FString& BehaviorPackage, FString& OutError);

    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static TArray<FCarnivalCrowdEntitySample> SampleLiveCrowdEntities(UWorld* World);
    /** Generate initial transforms for inspection without spawning or moving entities. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static TArray<FVector> PreviewCrowdSpawnLocations(UWorld* World, FString& OutError);
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static TArray<FString> DescribeCrowdLanes(UWorld* World);
    /** Changes only the named Carnival spawner's generator, retaining count and appearances. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static bool ConfigureDistinctCrowdSpawnPositions(AActor* Spawner, FString& OutError);
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static int32 GuardCrowdActorBeginPlay(UBlueprint* Blueprint, FString& OutError);
    /** Establish clothing pose links even when the outfit has no material overrides. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd")
    static int32 RepairCrowdClothingPoseLink(UBlueprint* Blueprint, FString& OutError);
    UFUNCTION(BlueprintCallable, Category="Carnival|Diagnostics")
    static FString GetMaterialFunctionStateId(UMaterialFunctionInterface* Function);
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
        FString& OutError, bool UseOwnedCrowdActor = false);

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
