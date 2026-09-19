#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalTypes.h"
#include "CarnivalActivityZone.h"
#include "CarnivalGuestLibrary.generated.h"

/**
 * Helpers for mapping a guest's role/job to display name, staff classification,
 * and the activity zone they belong to.
 */
UCLASS()
class CARNIVALPOPULATION_API UCarnivalGuestLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Carnival|Role")
    static FText GetRoleDisplayName(ECarnivalGuestRole Role);

    UFUNCTION(BlueprintPure, Category="Carnival|Role")
    static bool IsStaff(ECarnivalGuestRole Role);

    UFUNCTION(BlueprintPure, Category="Carnival|Role")
    static ECarnivalActivityType GetRoleActivityType(ECarnivalGuestRole Role);

    UFUNCTION(BlueprintPure, Category="Carnival|Role")
    static TArray<ECarnivalGuestRole> GetAllRoles();
};
