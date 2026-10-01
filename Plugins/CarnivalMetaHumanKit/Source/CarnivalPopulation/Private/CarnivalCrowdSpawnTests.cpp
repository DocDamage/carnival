#if WITH_DEV_AUTOMATION_TESTS
#include "CarnivalCrowdSpawnGenerator.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalCrowdSpawnSpacingTest, "Carnival.Crowd.DistinctLaneSpawnPositions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalCrowdSpawnSpacingTest::RunTest(const FString&)
{
    auto* Generator = NewObject<UCarnivalCrowdSpawnGenerator>();
    FZoneGraphStorage Storage;
    auto AddLane = [&](FVector Start, FVector End, float Width, FZoneGraphTagMask Tags = FZoneGraphTagMask(1))
    {
        auto& Lane = Storage.Lanes.AddDefaulted_GetRef();
        Lane.Width = Width; Lane.Tags = Tags; Lane.PointsBegin = Storage.LanePoints.Num();
        Storage.LanePoints.Append({Start, End});
        Storage.LaneTangentVectors.Append({(End-Start).GetSafeNormal(), (End-Start).GetSafeNormal()});
        Storage.LaneUpVectors.Append({FVector::UpVector, FVector::UpVector});
        Storage.LanePointProgressions.Append({0.f, static_cast<float>(FVector::Distance(Start, End))});
        Lane.PointsEnd = Storage.LanePoints.Num();
    };
    // Actual Carnival loop dimensions, with overlapping lane-width areas at four corners.
    AddLane({0,0,114}, {2000,0,114}, 600);
    AddLane({2000,0,114}, {2000,2000,114}, 600);
    AddLane({2000,2000,114}, {0,2000,114}, 600);
    AddLane({0,2000,114}, {0,0,114}, 600);
    TArray<FVector> Positions;
    Generator->AppendLaneCandidates(Storage, Positions);
    const int32 Capacity = Positions.Num();
    TestTrue(TEXT("Existing lane area fits all 240 guests without repeats"), Capacity >= 240);
    auto AllSpaced = [&]()
    {
        for (int32 A = 0; A < Positions.Num(); ++A)
            for (int32 B = A + 1; B < Positions.Num(); ++B)
                if (FVector::DistSquaredXY(Positions[A], Positions[B]) < 9999.9) return false;
        return true;
    };
    TestTrue(TEXT("Every candidate, including corner overlaps, is at least 100cm apart"), AllSpaced());
    TestTrue(TEXT("Selecting the requested density succeeds"), Generator->SelectLocations(Positions, 240, FRandomStream(11)));
    TestEqual(TEXT("Exactly 240 spawn locations supplied"), Positions.Num(), 240);
    TestTrue(TEXT("Selected positions remain spaced"), AllSpaced());
    Positions.Reset();
    Generator->AppendLaneCandidates(Storage, Positions);
    TestFalse(TEXT("Exceeding capacity is rejected rather than recycling locations"), Generator->SelectLocations(Positions, Capacity+1, FRandomStream(11)));
    TestEqual(TEXT("Insufficient capacity supplies no partial crowd"), Positions.Num(), 0);
    Storage.Reset();
    AddLane({0,0,114}, {1000,0,114}, 79);
    AddLane({0,1000,114}, {1000,1000,114}, 600, FZoneGraphTagMask(2));
    Generator->AppendLaneCandidates(Storage, Positions);
    TestEqual(TEXT("Too narrow and non-pedestrian lanes are excluded"), Positions.Num(), 0);
    AddLane({0,2000,114}, {1000,2000,114}, 80);
    Generator->AppendLaneCandidates(Storage, Positions);
    TestEqual(TEXT("An exactly one-person-wide lane gets one centered row"), Positions.Num(), 10);
    TestTrue(TEXT("Agent bodies remain inside the lane boundary"), Positions.ContainsByPredicate([](const FVector& P) { return P.Y == 2000; }));
    Generator->Spacing = 0.f;
    Positions.Reset(); Generator->AppendLaneCandidates(Storage, Positions);
    TestEqual(TEXT("Invalid spacing produces no candidates or infinite loop"), Positions.Num(), 0);
    return true;
}
#endif
