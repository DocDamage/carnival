#include "CarnivalCrowdSpawnGenerator.h"
#include "Engine/World.h"
#include "MassSpawnLocationProcessor.h"
#include "ZoneGraphData.h"
#include "ZoneGraphQuery.h"
#include "ZoneGraphSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogCarnivalCrowdSpawn, Log, All);

UCarnivalCrowdSpawnGenerator::UCarnivalCrowdSpawnGenerator()
{
    LaneFilter.AllTags = FZoneGraphTagMask(1);
}

void UCarnivalCrowdSpawnGenerator::AppendLaneCandidates(const FZoneGraphStorage& Storage, TArray<FVector>& Locations) const
{
    if (!FMath::IsFinite(Spacing) || !FMath::IsFinite(AgentRadius) || Spacing < AgentRadius * 2.f || AgentRadius <= 0.f) return;
    for (int32 Index = 0; Index < Storage.Lanes.Num(); ++Index)
    {
        const auto& Lane = Storage.Lanes[Index];
        if (!LaneFilter.Pass(Lane.Tags) || !FMath::IsFinite(Lane.Width) || Lane.Width < 2.f * AgentRadius || Lane.GetNumPoints() < 2) continue;
        float Length = 0.f;
        if (!UE::ZoneGraph::Query::GetLaneLength(Storage, Index, Length) || !FMath::IsFinite(Length)) continue;
        const float HalfUsableWidth = Lane.Width * .5f - AgentRadius;
        const int32 Columns = FMath::FloorToInt(2.f * HalfUsableWidth / Spacing) + 1;
        for (float Distance = Spacing * .5f; Distance <= Length - Spacing * .5f; Distance += Spacing)
        {
            FZoneGraphLaneLocation Center;
            if (!UE::ZoneGraph::Query::CalculateLocationAlongLane(Storage, Index, Distance, Center)) continue;
            const FVector Right = (Center.Direction ^ Center.Up).GetSafeNormal();
            for (int32 Column = 0; Column < Columns; ++Column)
            {
                const float Offset = (Column - (Columns - 1) * .5f) * Spacing;
                const FVector Point = Center.Position + Right * Offset;
                if (Point.ContainsNaN()) continue;
                // Mass pedestrian avoidance operates in XY. Check all lanes/storage together,
                // so intersecting or connected lanes cannot introduce duplicate spawn slots.
                if (!Locations.ContainsByPredicate([&](const FVector& Existing)
                    { return FVector::DistSquaredXY(Point, Existing) < FMath::Square(Spacing) - .01f; }))
                    Locations.Add(Point);
            }
        }
    }
}

bool UCarnivalCrowdSpawnGenerator::SelectLocations(TArray<FVector>& Locations, int32 Count, const FRandomStream& Random) const
{
    if (Count < 0 || Locations.Num() < Count) { Locations.Reset(); return false; }
    for (int32 Index = Locations.Num() - 1; Index > 0; --Index)
        Locations.Swap(Index, Random.RandRange(0, Index));
    Locations.SetNum(Count);
    return true;
}

void UCarnivalCrowdSpawnGenerator::Generate(UObject& QueryOwner, TConstArrayView<FMassSpawnedEntityType> EntityTypes,
    int32 Count, FFinishedGeneratingSpawnDataSignature& Finished) const
{
    TArray<FMassEntitySpawnDataGeneratorResult> Results;
    auto* World = QueryOwner.GetWorld();
    const auto* Graph = World ? World->GetSubsystem<UZoneGraphSubsystem>() : nullptr;
    if (Count <= 0) { Finished.Execute(Results); return; }
    if (!Graph)
    {
        UE_LOG(LogCarnivalCrowdSpawn, Error, TEXT("Carnival crowd cannot spawn: no ZoneGraph subsystem"));
        Finished.Execute(Results);
        return;
    }
    TArray<FVector> Locations;
    for (const auto& Registered : Graph->GetRegisteredZoneGraphData())
        if (Registered.bInUse && Registered.ZoneGraphData)
            AppendLaneCandidates(Registered.ZoneGraphData->GetStorage(), Locations);
    const int32 Capacity = Locations.Num();
    if (!SelectLocations(Locations, Count, FRandomStream(GetRandomSelectionSeed())))
    {
        UE_LOG(LogCarnivalCrowdSpawn, Error, TEXT("Carnival crowd cannot spawn %d guests: only %d distinct spaced lane positions"), Count, Capacity);
        Finished.Execute(Results);
        return;
    }
    BuildResultsFromEntityTypes(Count, EntityTypes, Results);
    int32 LocationIndex = 0;
    for (auto& Result : Results)
    {
        Result.SpawnDataProcessor = UMassSpawnLocationProcessor::StaticClass();
        Result.SpawnData.InitializeAs<FMassTransformsSpawnData>();
        auto& Data = Result.SpawnData.GetMutable<FMassTransformsSpawnData>();
        Data.Transforms.Reserve(Result.NumEntities);
        for (int32 Index = 0; Index < Result.NumEntities; ++Index)
            Data.Transforms.Emplace(Locations[LocationIndex++]);
    }
    UE_LOG(LogCarnivalCrowdSpawn, Display, TEXT("Carnival crowd spawning %d guests at distinct positions (capacity %d, spacing %.0f cm)"), LocationIndex, Capacity, Spacing);
    Finished.Execute(Results);
}
