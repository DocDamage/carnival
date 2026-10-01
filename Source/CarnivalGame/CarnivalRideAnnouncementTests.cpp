#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Sound/SoundWave.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalAnnouncementQueueTest, "Carnival.Rides.AnnouncementQueueSafety",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalAnnouncementQueueTest::RunTest(const FString&)
{
    UClass* Class = LoadClass<AActor>(nullptr, TEXT("/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/BP_Rides_Parent.BP_Rides_Parent_C"));
    if (!TestNotNull(TEXT("Actual imported ride parent loads"), Class)) return false;
    auto* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("AnnouncementQueueSafety"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    AActor* Ride = World->SpawnActor<AActor>(Class);
    if (!TestNotNull(TEXT("Parent ride spawns"), Ride)) return false;
    auto* SourceProperty = FindFProperty<FArrayProperty>(Class, TEXT("announcementsToPlay"));
    auto* QueueProperty = FindFProperty<FArrayProperty>(Class, TEXT("announcementsToPlay_temp"));
    auto* ElapsedProperty = FindFProperty<FNumericProperty>(Class, TEXT("timeElapsed"));
    auto* DelayProperty = FindFProperty<FNumericProperty>(Class, TEXT("announcementSelectedDelay"));
    UFunction* Event = Ride->FindFunction(TEXT("CustomEvent"));
    UAudioComponent* Audio = nullptr;
    TArray<UAudioComponent*> Components; Ride->GetComponents(Components);
    for (auto* Component : Components) if (Component->GetFName() == TEXT("AnnouncementAudio")) Audio = Component;
    if (!TestNotNull(TEXT("Source list exposed"), SourceProperty) || !TestNotNull(TEXT("Playback queue exposed"), QueueProperty)
        || !TestNotNull(TEXT("Elapsed timer exposed"), ElapsedProperty) || !TestNotNull(TEXT("Selected delay exposed"), DelayProperty)
        || !TestNotNull(TEXT("Actual timer event exposed"), Event) || !TestNotNull(TEXT("Announcement audio component exists"), Audio)) return false;
    if (!TestEqual(TEXT("Announcement event has no parameters"), Event->NumParms, uint8(0))) return false;
    auto* SourceInner = CastField<FObjectPropertyBase>(SourceProperty->Inner);
    auto* QueueInner = CastField<FObjectPropertyBase>(QueueProperty->Inner);
    if (!TestNotNull(TEXT("Source contains sound references"), SourceInner) || !TestNotNull(TEXT("Queue contains sound references"), QueueInner)) return false;
    FScriptArrayHelper Source(SourceProperty, SourceProperty->ContainerPtrToValuePtr<void>(Ride));
    FScriptArrayHelper Queue(QueueProperty, QueueProperty->ContainerPtrToValuePtr<void>(Ride));
    auto* SoundA = NewObject<USoundWave>(Ride); SoundA->Duration = 1.f;
    auto* SoundB = NewObject<USoundWave>(Ride); SoundB->Duration = 1.f;
    auto Add = [](FScriptArrayHelper& Array, FObjectPropertyBase* Inner, UObject* Value)
    {
        const int32 Index = Array.AddValue(); Inner->SetObjectPropertyValue(Array.GetRawPtr(Index), Value);
    };
    auto Invoke = [&]()
    {
        Audio->Stop();
        ElapsedProperty->SetFloatingPointPropertyValue(ElapsedProperty->ContainerPtrToValuePtr<void>(Ride), 42.);
        DelayProperty->SetFloatingPointPropertyValue(DelayProperty->ContainerPtrToValuePtr<void>(Ride), 0.);
        Ride->ProcessEvent(Event, nullptr);
        return ElapsedProperty->GetFloatingPointPropertyValue(ElapsedProperty->ContainerPtrToValuePtr<void>(Ride));
    };
    Source.EmptyValues(); Queue.EmptyValues();
    TestEqual(TEXT("Empty source/queue resets elapsed timer safely"), Invoke(), 0.);
    TestEqual(TEXT("Empty source remains empty"), Source.Num(), 0);
    TestEqual(TEXT("Empty queue remains empty"), Queue.Num(), 0);
    Add(Queue, QueueInner, SoundA);
    Invoke();
    TestTrue(TEXT("Populated queue still assigns its valid sound"), Audio->Sound == SoundA);
    TestEqual(TEXT("Played queue entry is consumed"), Queue.Num(), 0);
    Add(Source, SourceInner, SoundA); Add(Source, SourceInner, SoundB);
    Invoke();
    TestEqual(TEXT("Exhausted queue refills two entries and consumes one"), Queue.Num(), 1);
    TestTrue(TEXT("Refilled playback selects an authored source sound"), Audio->Sound == SoundA || Audio->Sound == SoundB);
    Invoke();
    TestEqual(TEXT("Second source entry is consumed without premature refill"), Queue.Num(), 0);
    Invoke();
    TestEqual(TEXT("Playback refills again after exhaustion"), Queue.Num(), 1);
    TestEqual(TEXT("Reusable source list retains both sounds"), Source.Num(), 2);
    Source.EmptyValues(); Queue.EmptyValues();
    TestEqual(TEXT("Removing content after playback restores safe empty behavior"), Invoke(), 0.);
    return true;
}
#endif
