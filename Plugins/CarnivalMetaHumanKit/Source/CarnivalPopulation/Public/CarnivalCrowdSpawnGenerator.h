#pragma once

#include "MassEntitySpawnDataGeneratorBase.h"
#include "ZoneGraphTypes.h"
#include "CarnivalCrowdSpawnGenerator.generated.h"

/** Initial lane positions only; guest movement remains owned by Mass navigation. */
UCLASS(BlueprintType, meta=(DisplayName="Carnival Spaced Pedestrian Spawn Points"))
class CARNIVALPOPULATION_API UCarnivalCrowdSpawnGenerator : public UMassEntitySpawnDataGeneratorBase
{
    GENERATED_BODY()
public:
    UCarnivalCrowdSpawnGenerator();
    virtual void Generate(UObject& QueryOwner, TConstArrayView<FMassSpawnedEntityType> EntityTypes,
        int32 Count, FFinishedGeneratingSpawnDataSignature& Finished) const override;

    /** Append candidates across lane width, rejecting overlaps including lane intersections. */
    void AppendLaneCandidates(const FZoneGraphStorage& Storage, TArray<FVector>& Locations) const;
    /** All-or-nothing selection: never recycle a position or silently reduce density. */
    bool SelectLocations(TArray<FVector>& Locations, int32 Count, const FRandomStream& Random) const;

    UPROPERTY(EditAnywhere, Category="Spawn", meta=(ClampMin="80"))
    float Spacing = 100.f;
    UPROPERTY(EditAnywhere, Category="Spawn", meta=(ClampMin="1"))
    float AgentRadius = 40.f;
    UPROPERTY(EditAnywhere, Category="Spawn")
    FZoneGraphTagFilter LaneFilter;
};
