#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalLayoutLibrary.generated.h"

UCLASS()
class CARNIVALPOPULATION_API UCarnivalLayoutLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Carnival|Layout")
    static TArray<FTransform> GenerateRowLayout(int32 SeatCount, float SpacingCm, FVector LocalOrigin, FRotator LocalRotation);

    UFUNCTION(BlueprintPure, Category="Carnival|Layout")
    static TArray<FTransform> GenerateGridLayout(int32 Rows, int32 Columns, float RowSpacingCm, float ColumnSpacingCm, FVector LocalOrigin, FRotator LocalRotation);

    UFUNCTION(BlueprintPure, Category="Carnival|Layout")
    static TArray<FTransform> GenerateRadialLayout(int32 SeatCount, float RadiusCm, float StartAngleDegrees, bool bFaceOutward);

    UFUNCTION(BlueprintPure, Category="Carnival|Layout")
    static TArray<FTransform> GenerateSerpentineQueue(int32 SlotCount, int32 SlotsPerRow, float SlotSpacingCm, float RowSpacingCm, FVector LocalOrigin);
};
