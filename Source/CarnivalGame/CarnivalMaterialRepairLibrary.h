#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalMaterialRepairLibrary.generated.h"

/** Editor-only recovery of graph edges in project-owned material duplicates. */
UCLASS()
class CARNIVALGAME_API UCarnivalMaterialRepairLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Empty result means every original edge was validated and restored. */
    UFUNCTION(BlueprintCallable, Category="Carnival|MaterialRepair")
    static TArray<FString> RestoreMaterialGraphConnections(UObject* Source, UObject* Destination);
};
