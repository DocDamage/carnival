#include "CarnivalAudioSettingsSubsystem.h"
#include "AudioDevice.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Misc/ConfigCacheIni.h"

namespace { constexpr const TCHAR* AudioSection = TEXT("Carnival.AudioSettings"); }

void UCarnivalAudioSettingsSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    LoadSavedVolume();
}

void UCarnivalAudioSettingsSubsystem::LoadSavedVolume()
{
    float Saved = 1.f;
    if (GConfig) GConfig->GetFloat(AudioSection, TEXT("MasterVolume"), Saved, GGameUserSettingsIni);
    SetMasterVolume(Saved, false);
}

void UCarnivalAudioSettingsSubsystem::SetMasterVolume(float Volume, bool bSave)
{
    MasterVolume = FMath::IsFinite(Volume) ? FMath::Clamp(Volume, 0.f, 1.f) : 1.f;
    if (bSave && GConfig)
    {
        GConfig->SetFloat(AudioSection, TEXT("MasterVolume"), MasterVolume, GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
    ApplyToWorld(GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr);
}

bool UCarnivalAudioSettingsSubsystem::ApplyToWorld(UWorld* World)
{
    if (!World) return false;
    FAudioDeviceHandle Device = World->GetAudioDevice();
    if (!Device.IsValid()) return false;
    Device->SetTransientPrimaryVolume(MasterVolume);
    return true;
}
