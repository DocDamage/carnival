#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalHauntedDoll.h"
#include "CarnivalDollAnimInstance.h"
#include "CarnivalMissionSubsystem.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/WorldSettings.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHauntedDollEncounterTest, "Carnival.HauntedDoll.Encounter",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FHauntedDollEncounterTest::RunTest(const FString&)
{
    UClass* DollClass = LoadClass<ACarnivalHauntedDoll>(nullptr,
        TEXT("/Game/Carnival/Characters/PossessedDoll/BP_PossessedDoll.BP_PossessedDoll_C"));
    if (!TestNotNull(TEXT("Reusable doll Blueprint loads"), DollClass)) return false;
    UGameInstance* GameInstance = NewObject<UGameInstance>(GEngine);
    GameInstance->InitializeStandalone(TEXT("DollAutomation"));
    UWorld* World = GameInstance->GetWorld();
    FURL URL;
    URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();

    auto Box = [&](const FVector& Position, const FVector& Extent)
    {
        AActor* Actor = World->SpawnActor<AActor>();
        UBoxComponent* Component = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component);
        Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll"));
        Component->RegisterComponent();
        Actor->SetActorLocation(Position);
        return Actor;
    };
    Box(FVector(0, 0, -20), FVector(3000, 3000, 20));
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACarnivalHauntedDoll* Doll = World->SpawnActor<ACarnivalHauntedDoll>(DollClass, FVector(0, 0, 74), FRotator::ZeroRotator, Spawn);
    ACharacter* Player = World->SpawnActor<ACharacter>(FVector(550, 0, 91), FRotator::ZeroRotator, Spawn);
    TSet<EDollEncounterState> States;
    float PeakRunSpeed = 0;
    auto Step = [&](float Seconds)
    {
        for (int32 I = 0; I < FMath::CeilToInt(Seconds * 60); ++I)
        {
            ++GFrameCounter;
            World->Tick(LEVELTICK_All, 1.f / 60.f);
            States.Add(Doll->EncounterState);
            if (Doll->EncounterState == EDollEncounterState::Chase)
                PeakRunSpeed = FMath::Max(PeakRunSpeed, static_cast<float>(Doll->GetVelocity().Size2D()));
        }
    };
    Step(.2f);
    TestNotNull(TEXT("Doll skeletal mesh"), Doll->GetMesh()->GetSkeletalMeshAsset());
    auto* Anim = Cast<UCarnivalDollAnimInstance>(Doll->GetMesh()->GetAnimInstance());
    TestNotNull(TEXT("Native animation controller initialized"), Anim);
    TestTrue(TEXT("Idle clip playing"), Anim && Anim->CurrentAnimation == Doll->IdleAnimation);
    TestTrue(TEXT("Idle bounds have doll proportions"), Doll->GetMesh()->Bounds.BoxExtent.Z > 40 && Doll->GetMesh()->Bounds.BoxExtent.Z < 100);

    Player->SetActorLocation(FVector(-300, 0, 91));
    TestFalse(TEXT("Player behind doll is outside detection cone"), Doll->ActivateForPlayer(Player));
    Player->SetActorLocation(FVector(950, 0, 91));
    TestFalse(TEXT("Player outside detection range"), Doll->ActivateForPlayer(Player));
    Player->SetActorLocation(FVector(550, 0, 91));
    AActor* Wall = Box(FVector(250, 0, 120), FVector(15, 150, 120));
    TestFalse(TEXT("Visibility wall blocks detection"), Doll->ActivateForPlayer(Player));
    Wall->Destroy();
    TestTrue(TEXT("Visible player starts encounter"), Doll->ActivateForPlayer(Player));
    TestEqual(TEXT("Notice state first"), Doll->EncounterState, EDollEncounterState::Notice);
    const FQuat HeadBefore = Doll->GetMesh()->GetSocketQuaternion(TEXT("head"));
    Step(.4f);
    const FQuat HeadAfter = Doll->GetMesh()->GetSocketQuaternion(TEXT("head"));
    TestTrue(TEXT("Animated head pose changes during notice"), HeadBefore.AngularDistance(HeadAfter) > .01);
    TestTrue(TEXT("Notice sequence selected"), Anim && Anim->CurrentAnimation == Doll->NoticeAnimation);
    for (int32 I=0; I<1000 && Doll->EncounterState != EDollEncounterState::Scare; ++I) Step(1.f / 60.f);
    TestTrue(TEXT("Walk state reached"), States.Contains(EDollEncounterState::Approach));
    TestTrue(TEXT("Run state reached"), States.Contains(EDollEncounterState::Chase));
    TestTrue(TEXT("Capsule actually runs at authored stride speed"), PeakRunSpeed > 90 && PeakRunSpeed < 110);
    TestEqual(TEXT("Proximity triggers scare"), Doll->EncounterState, EDollEncounterState::Scare);
    const FVector ScareStart = Doll->GetActorLocation();
    float ScarePeakZ = ScareStart.Z;
    for (int32 I=0; I<150; ++I)
    {
        Step(1.f / 60.f);
        ScarePeakZ=FMath::Max(ScarePeakZ, static_cast<float>(Doll->GetActorLocation().Z));
    }
    TestEqual(TEXT("Scare fires once"), Doll->ScareCount, 1);
    const float LungeDistance = Doll->GetActorLocation().X - ScareStart.X;
    TestTrue(TEXT("Authored lunge moves collision capsule forward"), LungeDistance > 25.f);
    TestTrue(TEXT("Authored hop moves collision capsule upward"), ScarePeakZ - ScareStart.Z > 10.f);
    TestEqual(TEXT("Scare ends in cooldown"), Doll->EncounterState, EDollEncounterState::Cooldown);
    TestFalse(TEXT("Cooldown prevents retrigger"), Doll->ActivateForPlayer(Player));
    Step(15.f);
    TestTrue(TEXT("Return state reached"), States.Contains(EDollEncounterState::Returning));
    TestEqual(TEXT("Encounter resets to idle"), Doll->EncounterState, EDollEncounterState::Idle);
    TestTrue(TEXT("Returned near home"), FVector::Dist2D(Doll->GetActorLocation(), Doll->HomeLocation) < 40.f);

    Doll->bEncounterEnabled=false;
    const float JumpStartZ=Doll->GetActorLocation().Z;
    float JumpPeakZ=JumpStartZ;
    TestTrue(TEXT("Jump action accepted"), Doll->PlayDollAction(Doll->JumpAnimation));
    for (int32 I=0; I<120; ++I)
    {
        Step(1.f/60.f);
        JumpPeakZ=FMath::Max(JumpPeakZ, static_cast<float>(Doll->GetActorLocation().Z));
    }
    TestTrue(TEXT("Manual jump lifts capsule"), JumpPeakZ-JumpStartZ > 15.f);
    TestTrue(TEXT("Jump lands near original floor"), FMath::Abs(Doll->GetActorLocation().Z-JumpStartZ) < 4.f);
    TestTrue(TEXT("RamsterZ retarget can play on same skeleton"), Doll->RamsterIdleAnimation && Doll->PlayDollAction(Doll->RamsterIdleAnimation));
    Step(.5f);
    TestTrue(TEXT("RamsterZ clip reaches animation controller"), Anim && Anim->CurrentAnimation == Doll->RamsterIdleAnimation);
    Doll->ResetEncounter();
    Step(.2f);
    Doll->bEncounterEnabled=true;
    Player->SetActorLocation(Doll->GetActorLocation()+FVector(300,0,15));
    Doll->SetActorRotation(FRotator::ZeroRotator);
    TestTrue(TEXT("A later encounter can activate"), Doll->ActivateForPlayer(Player));
    Wall=Box(Doll->GetActorLocation()+FVector(150,0,45),FVector(15,150,120));
    Step(4.f);
    TestFalse(TEXT("Lost sight cancels active pursuit"), Doll->EncounterState == EDollEncounterState::Chase || Doll->EncounterState == EDollEncounterState::Approach);
    TestEqual(TEXT("Hidden player is not scared through wall"), Doll->ScareCount, 1);
    AddInfo(FString::Printf(TEXT("Doll metrics: run=%.2f cm/s; lunge=%.2f cm; scare hop=%.2f cm; jump=%.2f cm"),
        PeakRunSpeed, LungeDistance, ScarePeakZ-ScareStart.Z, JumpPeakZ-JumpStartZ));
    World->EndPlay(EEndPlayReason::Quit);
    GameInstance->Shutdown();
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHauntedDollMissionScareTest, "Carnival.HauntedDoll.ScriptedMissionScare",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FHauntedDollMissionScareTest::RunTest(const FString&)
{
    UClass* DollClass = LoadClass<ACarnivalHauntedDoll>(nullptr,
        TEXT("/Game/Carnival/Characters/PossessedDoll/BP_PossessedDoll.BP_PossessedDoll_C"));
    UAnimSequence* HeadSnap = LoadObject<UAnimSequence>(nullptr,
        TEXT("/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Head_Snap.Doll_Head_Snap"));
    UAnimSequence* Lunge = LoadObject<UAnimSequence>(nullptr,
        TEXT("/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Jumpscare_Lunge.Doll_Jumpscare_Lunge"));
    if (!TestNotNull(TEXT("Doll Blueprint loads"), DollClass) || !HeadSnap || !Lunge)
    {
        AddError(TEXT("Mission scare animations must be present"));
        return false;
    }

    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("DollMissionScare"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL;
    URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();

    UCarnivalMissionSubsystem* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>();
    if (!TestNotNull(TEXT("Mission subsystem exists"), Mission)) return false;
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACarnivalHauntedDoll* Doll = World->SpawnActor<ACarnivalHauntedDoll>(DollClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    ACharacter* Player = World->SpawnActor<ACharacter>(FVector(250.f, 0.f, 0.f), FRotator::ZeroRotator, Spawn);
    if (!TestNotNull(TEXT("Mission doll spawns"), Doll) || !TestNotNull(TEXT("Scare witness spawns"), Player)) return false;
    Doll->MissionHeadSnapAnimation = HeadSnap;
    Doll->ScareAnimation = Lunge;
    Doll->bMissionControlledInstance = true;
    Doll->bEncounterEnabled = false;
    TestFalse(TEXT("Scare cannot begin before the music-box objective"), Doll->BeginScriptedMissionScare(Player));

    Mission->BeginStoryMission();
    Mission->ReportMansionArrival();
    Mission->CollectFoyerGlove();
    Mission->CollectStudyLogAndKey();
    Mission->ReportWorkerFound();
    Mission->RecoverMusicBox();

    TestTrue(TEXT("Music-box state starts the scripted scare"), Doll->BeginScriptedMissionScare(Player));
    TestFalse(TEXT("Mission doll cannot enter autonomous detection"), Doll->CanDetectPawn(Player));
    TestEqual(TEXT("Scripted scare counts once"), Doll->ScareCount, 1);
    for (int32 I = 0; I < 600 && Mission->GetMissionState() == ECarnivalStoryMissionState::PlayDollScare; ++I)
    {
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, 1.f / 60.f);
    }
    TestEqual(TEXT("Head snap, blackout, lunge, and aftermath return the objective to escape"),
        Mission->GetMissionState(), ECarnivalStoryMissionState::EscapeMansion);
    TestFalse(TEXT("Mission scare does not start an autonomous chase"), Doll->bEncounterEnabled);
    return true;
}
#endif
