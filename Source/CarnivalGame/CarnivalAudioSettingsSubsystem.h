#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CarnivalAudioSettingsSubsystem.generated.h"

/** Persistent user gain, applied to the game's audio device across map changes. */
UCLASS()
class CARNIVALGAME_API UCarnivalAudioSettingsSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    UPROPERTY(BlueprintReadOnly, Category="Audio") float MasterVolume = 1.f;
    UFUNCTION(BlueprintCallable, Category="Audio") void SetMasterVolume(float Volume, bool bSave = true);
    UFUNCTION(BlueprintCallable, Category="Audio") void LoadSavedVolume();
    UFUNCTION(BlueprintCallable, Category="Audio") bool ApplyToWorld(UWorld* World);
};
