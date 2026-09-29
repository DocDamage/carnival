#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "AudioDevice.h"
#include "AudioThread.h"
#include "CarnivalAudioSettingsSubsystem.h"
#include "CarnivalPlayerController.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "InputKeyEventArgs.h"

namespace
{
float ReadGain(const FAudioDeviceHandle& Device)
{
    float Gain = 1.f;
    FAudioThread::RunCommandOnAudioThread([Device, &Gain] { Gain = Device->GetTransientPrimaryVolume(); });
    FAudioCommandFence Fence; Fence.BeginFence(); Fence.Wait();
    return Gain;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalAudioSettingsTest, "Carnival.Audio.VolumePersistenceAndApplication",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalAudioSettingsTest::RunTest(const FString&)
{
    FAudioDeviceHandle OriginalDevice = GEngine->GetMainAudioDevice();
    const float OriginalGain = OriginalDevice.IsValid() ? ReadGain(OriginalDevice) : 1.f;
    const FString OriginalIni = GGameUserSettingsIni;
    GGameUserSettingsIni = FPaths::ProjectSavedDir() / TEXT("Automation/AudioSettingsTest.ini");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(GGameUserSettingsIni), true);
    GConfig->Add(GGameUserSettingsIni, FConfigFile());
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("AudioSettings"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT
    {
        if (OriginalDevice.IsValid()) { OriginalDevice->SetTransientPrimaryVolume(OriginalGain); FAudioCommandFence Fence; Fence.BeginFence(); Fence.Wait(); }
        World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World);
        GConfig->UnloadFile(GGameUserSettingsIni); IFileManager::Get().Delete(*GGameUserSettingsIni); GGameUserSettingsIni = OriginalIni;
    };
    const FURL URL;
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto* Audio = Instance->GetSubsystem<UCarnivalAudioSettingsSubsystem>();
    if (!TestNotNull(TEXT("Audio preferences subsystem exists"), Audio)) return false;
    Audio->SetMasterVolume(2.f, false);
    TestEqual(TEXT("Volume clamps above full gain"), Audio->MasterVolume, 1.f);
    Audio->SetMasterVolume(-1.f, false);
    TestEqual(TEXT("Volume clamps below mute"), Audio->MasterVolume, 0.f);
    Audio->SetMasterVolume(.37f);
    FString Contents;
    TestTrue(TEXT("Volume setting is written to disk"), FFileHelper::LoadFileToString(Contents, *GGameUserSettingsIni)
        && Contents.Contains(TEXT("Carnival.AudioSettings")) && Contents.Contains(TEXT("MasterVolume")));
    GConfig->UnloadFile(GGameUserSettingsIni); GConfig->LoadFile(GGameUserSettingsIni);
    auto* Reloaded = NewObject<UCarnivalAudioSettingsSubsystem>(Instance);
    Reloaded->LoadSavedVolume();
    TestTrue(TEXT("Fresh settings object reloads exact saved gain"), FMath::IsNearlyEqual(Reloaded->MasterVolume, .37f));
    TestFalse(TEXT("Missing audio world is not reported as applied"), Reloaded->ApplyToWorld(nullptr));
    FAudioDeviceHandle Device = World->GetAudioDevice();
    if (Device.IsValid())
    {
        Audio->SetMasterVolume(.25f, false);
        TestTrue(TEXT("Preference applies to the real audio device"), Audio->ApplyToWorld(World));
        TestTrue(TEXT("Audio thread receives master gain"), FMath::IsNearlyEqual(ReadGain(Device), .25f));
        Audio->SetMasterVolume(0.f, false);
        TestTrue(TEXT("Mute reaches the real audio device"), FMath::IsNearlyEqual(ReadGain(Device), 0.f));
        AddInfo(TEXT("ActualAudioDeviceApplication=verified (gain and mute read on audio thread)"));
    }
    else AddInfo(TEXT("ActualAudioDeviceApplication=unavailable; run without -nosound to verify device gain. Persistence/navigation still tested."));
    Audio->SetMasterVolume(.5f, false);
    auto* PC = World->SpawnActor<ACarnivalPlayerController>(); PC->InitInputSystem();
    PC->ToggleSettingsMenu(); PC->SettingsMenuSelection = 6;
    PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_DPad_Left, IE_Pressed, 1.f));
    TestTrue(TEXT("Paused controller navigation adjusts volume"), FMath::IsNearlyEqual(Audio->MasterVolume, .4f));
    PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_DPad_Down, IE_Pressed, 1.f));
    TestEqual(TEXT("Appended audio row wraps to first setting"), PC->SettingsMenuSelection, 0);
    PC->ToggleSettingsMenu();
    return true;
}
#endif
