#include "CarnivalLayoutLibrary.h"

TArray<FTransform> UCarnivalLayoutLibrary::GenerateRowLayout(int32 SeatCount, float SpacingCm, FVector LocalOrigin, FRotator LocalRotation)
{
    TArray<FTransform> Result;
    SeatCount = FMath::Max(0, SeatCount);
    Result.Reserve(SeatCount);

    const float CenterOffset = (SeatCount - 1) * 0.5f;
    for (int32 Index = 0; Index < SeatCount; ++Index)
    {
        const FVector Offset(0.0f, (Index - CenterOffset) * SpacingCm, 0.0f);
        Result.Emplace(LocalRotation, LocalOrigin + Offset);
    }
    return Result;
}

TArray<FTransform> UCarnivalLayoutLibrary::GenerateGridLayout(int32 Rows, int32 Columns, float RowSpacingCm, float ColumnSpacingCm, FVector LocalOrigin, FRotator LocalRotation)
{
    TArray<FTransform> Result;
    Rows = FMath::Max(0, Rows);
    Columns = FMath::Max(0, Columns);
    Result.Reserve(Rows * Columns);

    const float ColumnCenter = (Columns - 1) * 0.5f;
    for (int32 Row = 0; Row < Rows; ++Row)
    {
        for (int32 Column = 0; Column < Columns; ++Column)
        {
            const FVector Offset(Row * RowSpacingCm, (Column - ColumnCenter) * ColumnSpacingCm, 0.0f);
            Result.Emplace(LocalRotation, LocalOrigin + Offset);
        }
    }
    return Result;
}

TArray<FTransform> UCarnivalLayoutLibrary::GenerateRadialLayout(int32 SeatCount, float RadiusCm, float StartAngleDegrees, bool bFaceOutward)
{
    TArray<FTransform> Result;
    SeatCount = FMath::Max(0, SeatCount);
    if (SeatCount == 0)
    {
        return Result;
    }

    Result.Reserve(SeatCount);
    const float Step = 360.0f / static_cast<float>(SeatCount);
    for (int32 Index = 0; Index < SeatCount; ++Index)
    {
        const float Angle = StartAngleDegrees + Step * Index;
        const float Radians = FMath::DegreesToRadians(Angle);
        const FVector Location(FMath::Cos(Radians) * RadiusCm, FMath::Sin(Radians) * RadiusCm, 0.0f);
        const float Yaw = bFaceOutward ? Angle : Angle + 180.0f;
        Result.Emplace(FRotator(0.0f, Yaw, 0.0f), Location);
    }
    return Result;
}

TArray<FTransform> UCarnivalLayoutLibrary::GenerateSerpentineQueue(int32 SlotCount, int32 SlotsPerRow, float SlotSpacingCm, float RowSpacingCm, FVector LocalOrigin)
{
    TArray<FTransform> Result;
    SlotCount = FMath::Max(0, SlotCount);
    SlotsPerRow = FMath::Max(1, SlotsPerRow);
    Result.Reserve(SlotCount);

    for (int32 Index = 0; Index < SlotCount; ++Index)
    {
        const int32 Row = Index / SlotsPerRow;
        const int32 InRow = Index % SlotsPerRow;
        const bool bReverse = (Row % 2) == 1;
        const int32 OrderedSlot = bReverse ? (SlotsPerRow - 1 - InRow) : InRow;
        const FVector Offset(Row * RowSpacingCm, OrderedSlot * SlotSpacingCm, 0.0f);
        Result.Emplace(FRotator::ZeroRotator, LocalOrigin + Offset);
    }
    return Result;
}
