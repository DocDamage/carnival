#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MetaHumanInstance.h"
#include "MetaHumanCrowdPipeline.h"
#include "MetaHumanCharacterActorInterface.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalCrowdActorInitializationTest, "Carnival.Crowd.DelayedActorAppearance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalCrowdActorInitializationTest::RunTest(const FString&)
{
    UClass* Class = LoadClass<AActor>(nullptr, TEXT("/Game/Carnival/Crowd/Actors/BP_CarnivalCrowdActor.BP_CarnivalCrowdActor_C"));
    if (!TestNotNull(TEXT("Owned crowd actor loads"), Class)) return false;
    TestTrue(TEXT("Owned actor retains the MetaHuman appearance interface"), Class->ImplementsInterface(UMetaHumanCharacterActorInterface::StaticClass()));
    auto* Game = NewObject<UGameInstance>(GEngine);
    Game->InitializeStandalone(TEXT("CrowdActorInitialization"));
    UWorld* World = Game->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Game->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    AActor* Actor = World->SpawnActor<AActor>(Class);
    if (!TestNotNull(TEXT("Crowd actor begins play before an appearance exists, without runtime errors"), Actor)) return false;
    TestTrue(TEXT("Appearance initially remains unassigned"), IMetaHumanCharacterActorInterface::Execute_GetMetaHumanInstance(Actor) == nullptr);
    auto* Instance = LoadObject<UMetaHumanInstance>(nullptr, TEXT("/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean.MHI_Dean"));
    if (!TestNotNull(TEXT("Actual authored guest appearance loads"), Instance)) return false;
    const auto* Assembly = Instance->GetAssemblyOutput().GetPtr<FMetaHumanCrowdAssemblyOutput>();
    if (!TestNotNull(TEXT("Actual guest has crowd assembly output"), Assembly)) return false;
    if (!TestNotNull(TEXT("Actual guest face mesh exists"), Assembly->ActorFaceMesh.Get())) return false;
    IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(Actor, Instance);
    TestTrue(TEXT("Delayed appearance is assigned through the original event"), IMetaHumanCharacterActorInterface::Execute_GetMetaHumanInstance(Actor) == Instance);
    TArray<USkeletalMeshComponent*> Components; Actor->GetComponents(Components);
    auto AssignedFace = [&]() { return Components.ContainsByPredicate([&](const USkeletalMeshComponent* Component)
        { return Component->GetFName() == TEXT("Face") && Component->GetSkeletalMeshAsset() == Assembly->ActorFaceMesh; }); };
    TestTrue(TEXT("Delayed assignment assembles the actual guest face"), AssignedFace());
    IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(Actor, Instance);
    TestTrue(TEXT("Repeated appearance assignment retains the face mesh"), AssignedFace());
    IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(Actor, nullptr);
    TestTrue(TEXT("Clearing the instance safely skips assembly"), IMetaHumanCharacterActorInterface::Execute_GetMetaHumanInstance(Actor) == nullptr);
    IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(Actor, Instance);
    TestTrue(TEXT("A pooled actor can receive its appearance again"), AssignedFace());
    auto* Complete = LoadObject<UMetaHumanInstance>(nullptr, TEXT("/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Full_CasualFemale.MHI_Full_CasualFemale"));
    if (!TestNotNull(TEXT("Authored complete-outfit appearance loads"), Complete)) return false;
    const auto* CompleteAssembly = Complete->GetAssemblyOutput().GetPtr<FMetaHumanCrowdAssemblyOutput>();
    if (!TestNotNull(TEXT("Complete outfit has assembly output"), CompleteAssembly)) return false;
    auto CheckClothingLinks = [&](AActor* TargetActor, UMetaHumanInstance* Appearance, const TCHAR* Context)
    {
        IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(TargetActor, Appearance);
        TArray<USkeletalMeshComponent*> AssignedComponents; TargetActor->GetComponents(AssignedComponents);
        USkeletalMeshComponent* Body = nullptr;
        for (auto* Component : AssignedComponents) if (Component->GetFName() == TEXT("Body")) Body = Component;
        if (!TestNotNull(FString(Context) + TEXT(" body driver"), Body)) return;
        int32 ClothingCount = 0;
        for (auto* Component : AssignedComponents)
            if (Component->GetName().StartsWith(TEXT("Outfit")) && Component->GetSkeletalMeshAsset())
            {
                ++ClothingCount;
                TestTrue(FString(Context) + TEXT(" ") + Component->GetName() + TEXT(" follows body"), Component->LeaderPoseComponent.Get() == Body);
            }
        TestTrue(FString(Context) + TEXT(" contains clothing"), ClothingCount > 0);
    };
    // The complete outfit has no material overrides: its pose link must not depend on map iteration.
    AActor* FreshCompleteActor = World->SpawnActor<AActor>(Class);
    if (!TestNotNull(TEXT("Fresh actor for an empty-override complete outfit"), FreshCompleteActor)) return false;
    CheckClothingLinks(FreshCompleteActor, Complete, TEXT("Fresh complete-outfit assignment"));
    CheckClothingLinks(Actor, Complete, TEXT("Pooled parts to complete outfit"));
    CheckClothingLinks(Actor, Instance, TEXT("Pooled complete outfit to parts"));
    IMetaHumanCharacterActorInterface::Execute_SetMetaHumanInstance(Actor, nullptr);
    CheckClothingLinks(Actor, Complete, TEXT("Cleared pooled actor to complete outfit"));
    return true;
}
#endif
