#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "CarnivalMotorcycle.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Misc/ScopeExit.h"
#include "Engine/SkeletalMesh.h"
#include "CarnivalPlayerCharacter.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequence.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleBrakePriorityTest, "Carnival.Motorcycle.BrakePriority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleBrakePriorityTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleBrakeAutomation"));
    UWorld* World = Instance->GetWorld();
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>();
    if (!TestNotNull(TEXT("Motorcycle spawned"), Bike)) return false;
    for (int32 Hz : {30, 60, 120})
    {
        for (float InitialSpeed : {900.f, -900.f})
        {
            Bike->CurrentSpeed = InitialSpeed;
            Bike->InputThrottle(InitialSpeed > 0 ? 1.f : -1.f);
            Bike->InputBrake(1.f);
            for (int32 Frame = 0; Frame < Hz; ++Frame) Bike->Tick(1.f / Hz);
            TestTrue(FString::Printf(TEXT("Brake stops held throttle in either direction at %d Hz"), Hz),
                FMath::Abs(Bike->CurrentSpeed) < .1f);
        }
        Bike->CurrentSpeed = 900.f;
        Bike->InputThrottle(1.f);
        Bike->InputBrake(.5f);
        for (int32 Frame = 0; Frame < Hz/2; ++Frame) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Half brake preserves analog deceleration"), FMath::IsNearlyEqual(Bike->CurrentSpeed, 450.f, 1.f));
        const float BeforeRelease = Bike->CurrentSpeed;
        Bike->InputBrake(0.f);
        Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Throttle resumes after brake release"), Bike->CurrentSpeed > BeforeRelease);
    }
    Instance->Shutdown();
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleReverseTest, "Carnival.Motorcycle.BrakeReverse",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleReverseTest::RunTest(const FString&)
{
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleBrakeReverse"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto* Floor=World->SpawnActor<AActor>();
    auto* Box=NewObject<UBoxComponent>(Floor);
    Floor->SetRootComponent(Box); Box->SetBoxExtent(FVector(10000,10000,20));
    Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent(); Floor->SetActorLocation(FVector(0,0,-20));
    for (int32 Hz : {30,60,120})
    {
        auto* Bike=World->SpawnActor<ACarnivalMotorcycle>();
        Bike->CurrentSpeed=900.f; Bike->InputBrakeReverse(.5f);
        bool bStopped=false;
        for (int32 I=0; I<Hz*3; ++I)
        {
            Bike->Tick(1.f/Hz);
            if (FMath::IsNearlyZero(Bike->CurrentSpeed)) bStopped=true;
            if (Bike->CurrentSpeed<0.f && !bStopped) AddError(TEXT("Reverse began before reaching zero speed"));
        }
        TestTrue(TEXT("Analog reverse reaches half configured reverse speed"),FMath::IsNearlyEqual(Bike->CurrentSpeed,-Bike->ReverseSpeed*.5f,1.f));
        Bike->UnPossessed(); Bike->Tick(.1f);
        TestTrue(TEXT("Unpossessing clears reverse request"),FMath::IsNearlyEqual(Bike->CurrentSpeed,-Bike->ReverseSpeed*.5f+40.f,1.f));
        Bike->SetActorLocation(FVector(0,0,3000)); Bike->bIsAirborne=true; Bike->CurrentSpeed=0.f;
        Bike->InputBrakeReverse(1.f);
        for (int32 I=0; I<Hz; ++I) Bike->Tick(1.f/Hz);
        TestTrue(TEXT("L2 cannot propel a stationary airborne bike backwards"),FMath::IsNearlyZero(Bike->CurrentSpeed));
        Bike->Destroy();
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleRampLaunchTest, "Carnival.Motorcycle.RampLaunch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleRampLaunchTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleRampAutomation"));
    UWorld* World = Instance->GetWorld();
    AActor* Ramp = World->SpawnActor<AActor>();
    UBoxComponent* Surface = NewObject<UBoxComponent>(Ramp);
    Ramp->SetRootComponent(Surface);
    Surface->SetBoxExtent(FVector(200, 300, 20));
    Surface->SetCollisionProfileName(TEXT("BlockAll"));
    Surface->RegisterComponent();
    Ramp->SetActorLocation(FVector(-200, 0, -73.2));
    Ramp->SetActorRotation(FRotator(15, 0, 0));
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>();
    for (int32 Hz : {30, 60, 120})
    {
        // Keep the first ground probe on the ramp at every tested frame rate.
        // The tilted box's top ends before its axis-aligned outer bound.
        Bike->SetActorLocation(FVector(-80, 0, 0));
        Bike->SetActorRotation(FRotator::ZeroRotator);
        Bike->CurrentSpeed = 900.f;
        Bike->VerticalVelocity = 0.f;
        Bike->bIsAirborne = false;
        Bike->InputThrottle(900.f / Bike->MaxSpeed);
        Bike->Tick(1.f / Hz);
        TestTrue(FString::Printf(TEXT("Ramp takeoff persists at %d Hz"), Hz), Bike->bIsAirborne);
        TestTrue(TEXT("Launch retains upward velocity"), Bike->VerticalVelocity > 100.f);
        const float TakeoffZ = Bike->GetActorLocation().Z;
        Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Next frame rises from ramp"), Bike->GetActorLocation().Z > TakeoffZ);
    }
    Instance->Shutdown();
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleAccelerationTest, "Carnival.Motorcycle.AccelerationAndRelease",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleAccelerationTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleAccelerationAutomation"));
    UWorld* World = Instance->GetWorld();
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>();
    for (int32 Hz : {30, 60, 120})
    {
        Bike->CurrentSpeed = 0.f;
        Bike->InputThrottle(1.f);
        for (int32 Frame = 0; Frame < Hz; ++Frame) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("One second acceleration uses configured rate"),
            FMath::IsNearlyEqual(Bike->CurrentSpeed, Bike->Acceleration, 1.f));
        Bike->InputThrottle(.25f);
        for (int32 Frame = 0; Frame < Hz; ++Frame) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Analog throttle settles at requested speed"),
            FMath::IsNearlyEqual(Bike->CurrentSpeed, Bike->MaxSpeed * .25f, 1.f));
        Bike->InputThrottle(10.f);
        for (int32 Frame = 0; Frame < Hz * 3; ++Frame) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Out of range throttle cannot exceed maximum"),
            FMath::IsNearlyEqual(Bike->CurrentSpeed, Bike->MaxSpeed, 1.f));
        Bike->InputSteering(1.f);
        Bike->InputBrake(1.f);
        Bike->UnPossessed();
        const float Before = Bike->CurrentSpeed;
        const float Yaw = Bike->GetActorRotation().Yaw;
        for (int32 Frame = 0; Frame < Hz; ++Frame) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Loss of possession clears throttle and brake and coasts"),
            FMath::IsNearlyEqual(Bike->CurrentSpeed, Before - 400.f, 1.f));
        TestTrue(TEXT("Loss of possession clears steering"),
            FMath::IsNearlyEqual(Bike->GetActorRotation().Yaw, Yaw, .01f));
    }
    Instance->Shutdown();
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleBalanceTest, "Carnival.Motorcycle.BalanceAndGrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleBalanceTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleBalanceAutomation"));
    UWorld* World = Instance->GetWorld();
    AActor* Floor = World->SpawnActor<AActor>();
    UBoxComponent* Surface = NewObject<UBoxComponent>(Floor);
    Floor->SetRootComponent(Surface);
    Surface->SetBoxExtent(FVector(50000, 50000, 20));
    Surface->SetCollisionProfileName(TEXT("BlockAll"));
    Surface->RegisterComponent();
    Floor->SetActorLocation(FVector(0, 0, -20));
    for (int32 Hz : {30, 60, 120})
    {
        auto* Bike = World->SpawnActor<ACarnivalMotorcycle>();
        Bike->CurrentSpeed = 1200.f;
        Bike->InputThrottle(1.f);
        Bike->InputRiderBalance(1.f);
        for (int32 I = 0; I < Hz; ++I) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Pulling back raises front wheel"), Bike->GetActorRotation().Pitch > 25.f);
        TestTrue(TEXT("Wheelie does not add altitude or airborne state"),
            FMath::Abs(Bike->GetActorLocation().Z) < 1.f && !Bike->bIsAirborne);
        Bike->InputRiderBalance(0.f);
        for (int32 I = 0; I < Hz; ++I) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Releasing balance restores level ground attitude"), FMath::Abs(Bike->GetActorRotation().Pitch) < 2.f);
        Bike->InputHandbrake(true);
        Bike->InputSteering(1.f);
        for (int32 I = 0; I < Hz/2; ++I) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Rear brake turn produces controlled slip"), Bike->SlipAngle > 10.f && Bike->SlipAngle < 55.f);
        Bike->InputHandbrake(false);
        Bike->InputSteering(0.f);
        for (int32 I = 0; I < Hz/2; ++I) Bike->Tick(1.f / Hz);
        TestTrue(TEXT("Rear brake release recovers grip"), FMath::Abs(Bike->SlipAngle) < 1.f);
        Bike->Destroy();

        auto* NoseUp = World->SpawnActor<ACarnivalMotorcycle>();
        auto* NoseDown = World->SpawnActor<ACarnivalMotorcycle>();
        for (auto* AirBike : {NoseUp, NoseDown})
        {
            AirBike->SetActorLocation(FVector(0, 0, 1000));
            AirBike->CurrentSpeed = 900.f;
            AirBike->InputThrottle(900.f / AirBike->MaxSpeed);
            AirBike->bIsAirborne = true;
        }
        NoseUp->InputRiderBalance(1.f);
        NoseDown->InputRiderBalance(-1.f);
        for (int32 I = 0; I < Hz/2; ++I)
        {
            NoseUp->Tick(1.f / Hz);
            NoseDown->Tick(1.f / Hz);
        }
        TestTrue(TEXT("Balance pitches bike in either direction in air"),
            NoseUp->GetActorRotation().Pitch > 30.f && NoseDown->GetActorRotation().Pitch < -30.f);
        TestTrue(TEXT("Air pitch does not redirect flight velocity"),
            NoseUp->GetActorLocation().Equals(NoseDown->GetActorLocation(), .1f));
        NoseUp->InputRiderBalance(0.f);
        for (int32 I = 0; I < Hz*2; ++I) NoseUp->Tick(1.f / Hz);
        TestTrue(TEXT("Flight recovers to supported level landing"), !NoseUp->bIsAirborne
            && FMath::Abs(NoseUp->GetActorLocation().Z) < 2.f && FMath::Abs(NoseUp->GetActorRotation().Pitch) < 2.f);
        NoseUp->Destroy();
        NoseDown->Destroy();
    }
    Instance->Shutdown();
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleSavedCollisionTest, "Carnival.Motorcycle.SavedBodyCollision",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleSavedCollisionTest::RunTest(const FString&)
{
    UClass* BikeClass = LoadClass<ACarnivalMotorcycle>(nullptr,
        TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    if (!TestNotNull(TEXT("Saved bike Blueprint exists"), BikeClass)) return false;
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleSavedCollision"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto Box = [&](FVector Location, FVector Extent)
    {
        auto* Actor = World->SpawnActor<AActor>();
        auto* Component = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component);
        Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll"));
        Component->RegisterComponent();
        Actor->SetActorLocation(Location);
        return Actor;
    };
    Box(FVector(0,0,-20), FVector(5000,5000,20));
    Box(FVector(0,0,300), FVector(10,400,300));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>(BikeClass, FVector(-1000,0,0), FRotator::ZeroRotator, Spawn);
    if (!TestNotNull(TEXT("Saved bike spawned"), Bike)) return false;
    TestNotNull(TEXT("Saved mesh has physical body"), Bike->BikeMesh->GetPhysicsAsset());
    if (!TestNotNull(TEXT("Front wheel mesh is installed"), Bike->FrontWheel->GetStaticMesh().Get())
        || !TestNotNull(TEXT("Rear wheel mesh is installed"), Bike->RearWheel->GetStaticMesh().Get())) return false;
    TestTrue(TEXT("Front and rear axles align with travel axis"),
        Bike->FrontWheel->GetRelativeLocation().X > 60.f && Bike->RearWheel->GetRelativeLocation().X < -40.f);
    TestTrue(TEXT("Resting tyres meet ground plane"),
        FMath::Abs(Bike->FrontWheel->GetRelativeLocation().Z - Bike->WheelRadius) < .1f
        && FMath::Abs(Bike->RearWheel->GetRelativeLocation().Z - Bike->WheelRadius) < .1f);
    Bike->InputThrottle(1.f);
    Bike->CurrentSpeed = Bike->MaxSpeed;
    TestEqual(TEXT("Saved bike defaults to arcade"), Bike->PhysicsMode, EMotorcyclePhysicsMode::Arcade);
    AddInfo(TEXT("Reference bone: ") + Bike->BikeMesh->GetSkeletalMeshAsset()->GetRefSkeleton().GetRefBonePose()[0].ToHumanReadableString());
    AddInfo(TEXT("Live bone: ") + Bike->BikeMesh->GetBoneTransform(0).ToHumanReadableString());
    // Drive the movement update explicitly in the standalone automation world;
    // it has no viewport/game loop to dispatch the pawn tick reliably.
    Bike->SetActorTickEnabled(false);
    const FVector InitialLocation = Bike->GetActorLocation();
    Bike->Tick(1.f/60.f);
    const float FirstDistance = Bike->GetActorLocation().X - InitialLocation.X;
    const FQuat ExpectedRoll = FRotator(-FMath::RadiansToDegrees(FirstDistance/Bike->WheelRadius),0,0).Quaternion();
    TestTrue(TEXT("Wheel rolls around axle by distance over radius"),
        Bike->RearWheel->GetRelativeRotation().Quaternion().Equals(ExpectedRoll, .001f));
    for (int32 I=0; I<60; ++I)
    {
        Bike->Tick(1.f/60.f);
        ++GFrameCounter; World->Tick(LEVELTICK_All, 1.f/60.f);
    }
    AddInfo(FString::Printf(TEXT("Saved bike final location %s, speed %.2f, tick enabled %d, physics bodies %d"),
        *Bike->GetActorLocation().ToString(), Bike->CurrentSpeed, Bike->IsActorTickEnabled(), Bike->BikeMesh->Bodies.Num()));
    TestTrue(TEXT("Full-speed saved motorcycle stops before solid barrier"), Bike->GetActorLocation().X < -10.f);
    TestTrue(TEXT("Bike actually approached barrier"), Bike->GetActorLocation().X > -300.f);
    TestTrue(TEXT("Barrier impact removes forward speed"), FMath::Abs(Bike->CurrentSpeed) < 1.f);
    TestTrue(TEXT("Visible front tyre stays outside barrier"),
        Bike->FrontWheel->GetComponentLocation().X + Bike->WheelRadius <= -9.f);
    const FQuat StoppedWheel = Bike->RearWheel->GetRelativeRotation().Quaternion();
    Bike->Tick(1.f/60.f);
    TestTrue(TEXT("Blocked bike does not keep spinning tyres"),
        Bike->RearWheel->GetRelativeRotation().Quaternion().Equals(StoppedWheel,.001f));
    Bike->InputSteering(1.f);
    Bike->Tick(1.f/60.f);
    const FQuat SteerDelta = Bike->FrontWheel->GetRelativeRotation().Quaternion()
        * Bike->RearWheel->GetRelativeRotation().Quaternion().Inverse();
    TestTrue(TEXT("Front wheel adds steering independently of rolling"),
        SteerDelta.Equals(FRotator(0,28,0).Quaternion(),.001f));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleTyreContactTest, "Carnival.Motorcycle.TyreContact",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleTyreContactTest::RunTest(const FString&)
{
    UClass* BikeClass = LoadClass<ACarnivalMotorcycle>(nullptr,
        TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    if (!TestNotNull(TEXT("Saved bike class"),BikeClass)) return false;
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleTyreContact"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto Box = [&](FVector Location,FVector Extent)
    {
        AActor* Actor=World->SpawnActor<AActor>();
        UBoxComponent* Component=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component); Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll")); Component->RegisterComponent();
        Actor->SetActorLocation(Location);
        return Actor;
    };
    Box(FVector(0,0,-20),FVector(20000,20000,20));
    Box(FVector(0,0,300),FVector(10,400,300));
    const FRotator RampRotation(30,0,0);
    const FVector RampNormal=RampRotation.RotateVector(FVector::UpVector);
    const FVector RampTop(0,6000,1000+20/FMath::Cos(FMath::DegreesToRadians(30.f)));
    Box(FVector(0,6000,1000),FVector(10000,500,20))->SetActorRotation(RampRotation);
    Box(FVector(-1000,-6000,12),FVector(1000,500,12));
    Box(FVector(-1000,-10000,12),FVector(1000,500,12));
    Box(FVector(0,-10000,150),FVector(1000,500,5));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    for (int32 Hz : {30,60,120})
    {
        for (int32 Direction : {-1,1})
        {
            auto* Bike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(-Direction*1000,0,0),FRotator::ZeroRotator,Spawn);
            Bike->InputThrottle(Direction);
            Bike->CurrentSpeed=Direction>0 ? Bike->MaxSpeed : -Bike->ReverseSpeed;
            for (int32 I=0; I<Hz*3; ++I) Bike->Tick(1.f/Hz);
            const float TyreEdge=Direction>0 ? Bike->FrontWheel->GetComponentLocation().X+Bike->WheelRadius
                : Bike->RearWheel->GetComponentLocation().X-Bike->WheelRadius;
            AddInfo(FString::Printf(TEXT("%d Hz direction %d tyre edge %.3f speed %.3f"),Hz,Direction,TyreEdge,Bike->CurrentSpeed));
            TestTrue(TEXT("Forward and reverse tyres stop at wall face"),Direction>0 ? TyreEdge<=-9.f && TyreEdge>-12.f : TyreEdge>=9.f && TyreEdge<12.f);
            TestTrue(TEXT("Tyre impact stops speed"),FMath::Abs(Bike->CurrentSpeed)<1.f);
            Bike->Destroy();
        }
        auto* Bike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(0,2000,0),FRotator::ZeroRotator,Spawn);
        Bike->InputThrottle(1.f); Bike->InputRiderBalance(1.f); Bike->CurrentSpeed=1000.f;
        for (int32 I=0; I<Hz; ++I) Bike->Tick(1.f/Hz);
        const float RearBottom=Bike->RearWheel->GetComponentLocation().Z-Bike->WheelRadius;
        const float FrontBottom=Bike->FrontWheel->GetComponentLocation().Z-Bike->WheelRadius;
        AddInfo(FString::Printf(TEXT("%d Hz wheelie tyre bottoms rear %.3f front %.3f"),Hz,RearBottom,FrontBottom));
        TestTrue(TEXT("Wheelie keeps rear tyre supported"),FMath::Abs(RearBottom)<.5f && !Bike->bIsAirborne);
        TestTrue(TEXT("Wheelie raises visible front wheel"),FrontBottom>60.f);
        Bike->InputRiderBalance(0.f);
        for (int32 I=0; I<Hz; ++I) Bike->Tick(1.f/Hz);
        TestTrue(TEXT("Wheelie release returns both tyres to ground"),
            FMath::Abs(Bike->FrontWheel->GetComponentLocation().Z-Bike->WheelRadius)<1.f
            && FMath::Abs(Bike->RearWheel->GetComponentLocation().Z-Bike->WheelRadius)<1.f);
        Bike->Destroy();
        auto* Climber=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,RampTop,RampRotation,Spawn);
        Climber->InputThrottle(1.f); Climber->CurrentSpeed=Climber->MaxSpeed;
        for (int32 I=0; I<Hz; ++I) Climber->Tick(1.f/Hz);
        const float Travel=Climber->GetActorLocation().X-RampTop.X;
        const float Contact=FVector::DotProduct(RampNormal,Climber->RearWheel->GetComponentLocation()-RampTop)-Climber->WheelRadius;
        AddInfo(FString::Printf(TEXT("%d Hz 30 degree climb distance %.3f rear clearance %.3f"),Hz,Travel,Contact));
        TestTrue(TEXT("Saved bike climbs without body-sweep slowdown"),Travel>Climber->MaxSpeed*.95f);
        TestTrue(TEXT("Uphill rear tyre stays supported"),FMath::Abs(Contact)<1.f && !Climber->bIsAirborne);
        Climber->Destroy();
        auto* StepBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(-300,-6000,24),FRotator::ZeroRotator,Spawn);
        StepBike->CurrentSpeed=600.f; StepBike->InputThrottle(600.f/StepBike->MaxSpeed);
        for (int32 I=0; I<Hz; ++I) StepBike->Tick(1.f/Hz);
        AddInfo(FString::Printf(TEXT("%d Hz pavement step-down finish %s"),Hz,*StepBike->GetActorLocation().ToString()));
        TestTrue(TEXT("Bike rolls off raised pavement without embedding its rear body"),StepBike->GetActorLocation().X>290.f);
        TestTrue(TEXT("Step-down reaches lower ground"),FMath::Abs(StepBike->GetActorLocation().Z)<1.f && !StepBike->bIsAirborne);
        StepBike->Destroy();
        auto* UpBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(300,-6000,0),FRotator(0,180,0),Spawn);
        UpBike->CurrentSpeed=600.f; UpBike->InputThrottle(600.f/UpBike->MaxSpeed);
        for (int32 I=0; I<Hz; ++I) UpBike->Tick(1.f/Hz);
        AddInfo(FString::Printf(TEXT("%d Hz pavement step-up finish %s"),Hz,*UpBike->GetActorLocation().ToString()));
        TestTrue(TEXT("Bike rolls onto low pavement"),UpBike->GetActorLocation().X < -290.f);
        TestTrue(TEXT("Step-up rests on upper surface"),FMath::Abs(UpBike->GetActorLocation().Z-24.f)<1.f && !UpBike->bIsAirborne);
        UpBike->Destroy();
        auto* RoofBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(300,-10000,0),FRotator(0,180,0),Spawn);
        RoofBike->CurrentSpeed=600.f; RoofBike->InputThrottle(600.f/RoofBike->MaxSpeed);
        float HighestRoot=0.f;
        for (int32 I=0; I<Hz*2; ++I)
        {
            RoofBike->Tick(1.f/Hz);
            HighestRoot=FMath::Max(HighestRoot,float(RoofBike->GetActorLocation().Z));
        }
        TestTrue(TEXT("Low headroom prevents stepping through ceiling"),RoofBike->GetActorLocation().X>0.f && HighestRoot<15.f);
        RoofBike->Destroy();
        auto* TurningBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(0,12000,0),FRotator::ZeroRotator,Spawn);
        TurningBike->CurrentSpeed=TurningBike->MaxSpeed; TurningBike->InputThrottle(1.f); TurningBike->InputSteering(1.f);
        for (int32 I=0; I<Hz*2; ++I) TurningBike->Tick(1.f/Hz);
        AddInfo(FString::Printf(TEXT("%d Hz saved-bike full lean speed %.3f roll %.3f"),Hz,TurningBike->CurrentSpeed,TurningBike->GetActorRotation().Roll));
        TestTrue(TEXT("Leaning through a flat-ground turn does not collide with the floor"),TurningBike->CurrentSpeed>TurningBike->MaxSpeed*.95f);
        TurningBike->Destroy();
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleAirCollisionTest, "Carnival.Motorcycle.AirCollision",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleAirCollisionTest::RunTest(const FString&)
{
    UClass* BikeClass=LoadClass<ACarnivalMotorcycle>(nullptr,TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    if (!TestNotNull(TEXT("Saved bike class"),BikeClass)) return false;
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleAirCollision"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    auto Box=[&](FVector Location,FVector Extent)
    {
        auto* Actor=World->SpawnActor<AActor>();
        auto* Component=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component); Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll")); Component->RegisterComponent();
        Actor->SetActorLocation(Location);
    };
    Box(FVector(0,0,-5),FVector(5000,10000,5));
    Box(FVector(0,3000,1000),FVector(1000,500,10));
    Box(FVector(10,6000,750),FVector(10,500,750));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    for (int32 Hz : {30,60,120})
    {
        for (float Pitch : {-45.f,0.f,45.f})
        {
            auto* Bike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(0,0,900),FRotator(Pitch,0,0),Spawn);
            Bike->bIsAirborne=true; Bike->VerticalVelocity=-6000.f;
            float MinimumTyre=900.f;
            for (int32 I=0; I<Hz*2; ++I)
            {
                Bike->Tick(1.f/Hz);
                MinimumTyre=FMath::Min(MinimumTyre,float(FMath::Min(Bike->FrontWheel->GetComponentLocation().Z,
                    Bike->RearWheel->GetComponentLocation().Z)-Bike->WheelRadius));
            }
            AddInfo(FString::Printf(TEXT("%d Hz pitch %.0f fast landing minimum tyre %.3f final %s"),Hz,Pitch,MinimumTyre,*Bike->GetActorLocation().ToString()));
            TestTrue(TEXT("Fast fall does not tunnel through thin floor"),MinimumTyre>=-.5f);
            TestTrue(TEXT("Pitched landing settles on floor"),!Bike->bIsAirborne && FMath::Abs(Bike->GetActorLocation().Z)<1.f);
            Bike->Destroy();
        }
        auto* NearFloor=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(0,0,100),FRotator::ZeroRotator,Spawn);
        NearFloor->bIsAirborne=true; NearFloor->Tick(1.f/Hz);
        TestTrue(TEXT("Ground probe does not prematurely land a falling bike"),NearFloor->bIsAirborne && NearFloor->GetActorLocation().Z>90.f);
        NearFloor->Destroy();
        auto* Jumper=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(0,3000,700),FRotator::ZeroRotator,Spawn);
        Jumper->bIsAirborne=true; Jumper->VerticalVelocity=3000.f;
        float HighestBody=0.f;
        for (int32 I=0; I<Hz*2; ++I)
        {
            Jumper->Tick(1.f/Hz);
            HighestBody=FMath::Max(HighestBody,float(Jumper->BikeMesh->CalcBounds(Jumper->BikeMesh->GetComponentTransform()).GetBox().Max.Z));
        }
        AddInfo(FString::Printf(TEXT("%d Hz ceiling highest body %.3f"),Hz,HighestBody));
        TestTrue(TEXT("Rising chassis stops below thin ceiling"),HighestBody<=990.5f);
        TestTrue(TEXT("Ceiling impact allows subsequent fall"),Jumper->GetActorLocation().Z<100.f);
        Jumper->Destroy();
        auto* WallBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(-114.0586,6000,600),FRotator::ZeroRotator,Spawn);
        WallBike->bIsAirborne=true; WallBike->VerticalVelocity=-1000.f;
        for (int32 I=0; I<Hz*2; ++I) WallBike->Tick(1.f/Hz);
        TestTrue(TEXT("Bike falls alongside touching wall without sticking"),!WallBike->bIsAirborne && FMath::Abs(WallBike->GetActorLocation().Z)<1.f);
        WallBike->Destroy();
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleDismountTest, "Carnival.Motorcycle.SafeDismount",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleDismountTest::RunTest(const FString&)
{
    UClass* BikeClass=LoadClass<ACarnivalMotorcycle>(nullptr,TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    UClass* RiderClass=LoadClass<ACarnivalPlayerCharacter>(nullptr,TEXT("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C"));
    if (!BikeClass || !RiderClass) { AddError(TEXT("Saved bike and rider required")); return false; }
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleSafeDismount"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto Box=[&](FVector Location,FVector Extent)
    {
        auto* Actor=World->SpawnActor<AActor>();
        auto* Component=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component); Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll")); Component->RegisterComponent();
        Actor->SetActorLocation(Location); return Actor;
    };
    AActor* Floor=Box(FVector(0,0,-20),FVector(1000,1000,20));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Bike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    auto* Rider=World->SpawnActor<ACarnivalPlayerCharacter>(RiderClass,FVector(0,-60,98.195294),FRotator::ZeroRotator,Spawn);
    auto* Controller=World->SpawnActor<APlayerController>();
    int32 ExitCaptureIndex = 0;
    auto AdvanceExit=[&](bool bCaptureGraph=false)
    {
        float MaxStep=0.f;
        UAnimMontage* CapturedMontage = nullptr;
        for (int32 I=0; I<120 && Bike->bDismounting; ++I)
        {
            const FVector Before=Rider->GetActorLocation();
            ++GFrameCounter; Rider->GetMesh()->TickAnimation(1.f/60.f,false);
            Rider->GetMesh()->RefreshBoneTransforms(); Bike->Tick(1.f/60.f); Rider->Tick(1.f/60.f);
            MaxStep=FMath::Max(MaxStep,float(FVector::Distance(Before,Rider->GetActorLocation())));
            UAnimInstance* Anim=Rider->GetMesh()->GetAnimInstance();
            if (Anim && Anim->Montage_IsPlaying(Rider->DismountLeftMontage)) CapturedMontage=Rider->DismountLeftMontage;
            else if (Anim && Anim->Montage_IsPlaying(Rider->DismountRightMontage)) CapturedMontage=Rider->DismountRightMontage;
            if (bCaptureGraph && Anim && CapturedMontage && (I%10==0 || !Bike->bDismounting))
            {
                const float MontageTime=Anim->Montage_GetPosition(CapturedMontage);
                const bool bLeftExit=CapturedMontage==Rider->DismountLeftMontage;
                if (MontageTime>=.30f && MontageTime<=.70f)
                {
                    const FVector SupportFoot=Rider->GetMesh()->GetBoneLocation(bLeftExit ? TEXT("foot_l") : TEXT("foot_r"));
                    const FVector Peg=Bike->GetActorTransform().TransformPosition(FVector(-8.f,bLeftExit ? -30.f : 30.f,46.f));
                    const float PegGap=FVector::Distance(SupportFoot,Peg);
                    AddInfo(FString::Printf(TEXT("Live support foot-to-peg gap %.3f cm"),PegGap));
                    TestTrue(TEXT("Planted dismount foot stays on its peg through live graph playback"),PegGap<2.f);
                }
                AddInfo(FString::Printf(TEXT("Live dismount graph %d frame %d time %.3f root %s pelvis %s head %s feet %s / %s"),
                    ExitCaptureIndex,I,MontageTime,*Rider->GetActorLocation().ToString(),
                    *Rider->GetMesh()->GetBoneLocation(TEXT("pelvis")).ToString(),
                    *Rider->GetMesh()->GetBoneLocation(TEXT("head")).ToString(),
                    *Rider->GetMesh()->GetBoneLocation(TEXT("foot_l")).ToString(),
                    *Rider->GetMesh()->GetBoneLocation(TEXT("foot_r")).ToString()));
            }
            if (Bike->bDismounting)
                TestTrue(TEXT("Staged exit retains possession and disabled collision until complete"),Controller->GetPawn()==Bike
                    && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
        }
        ++ExitCaptureIndex;
        AddInfo(FString::Printf(TEXT("Maximum dismount capsule step %.3f cm"),MaxStep));
        TestTrue(TEXT("Dismount advances continuously without an exit teleport"),MaxStep<15.f);
    };
    auto ReturnToLeftApproach=[&]()
    {
        Rider->SetActorLocationAndRotation(FVector(0,-60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    };
    Controller->Possess(Rider); Bike->Mount(Rider,true);
    const FVector Seated=Rider->GetActorLocation();
    Bike->Dismount();
    TestTrue(TEXT("Exit starts animation while rider remains possessed on bike"),Bike->bDismounting && Controller->GetPawn()==Bike
        && Rider->GetActorLocation().Equals(Seated,.1f) && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
    TestTrue(TEXT("Left exit plays matching animation"),Rider->GetMesh()->GetAnimInstance()->Montage_IsPlaying(Rider->DismountLeftMontage));
    AdvanceExit(true);
    TestTrue(TEXT("Clear exit restores rider possession"),Controller->GetPawn()==Rider && Bike->CurrentRider==nullptr);
    TestTrue(TEXT("Clear exit places rider beside bike on floor"),Rider->GetActorLocation().Y<-100.f
        && FMath::Abs(Rider->GetActorLocation().Z-Rider->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()-2.f)<.1f);
    TestTrue(TEXT("Exit restores walking and collision"),Rider->GetCharacterMovement()->MovementMode==MOVE_Walking
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);

	Bike->Mount(Rider,true); Bike->Dismount();
    AActor* NewObstacle=Box(FVector(0,-120,200),FVector(30,10,200));
    AdvanceExit();
    TestTrue(TEXT("New exit obstruction cancels staging and restores mounted ownership"),!Bike->bDismounting
        && Bike->CurrentRider==Rider && Controller->GetPawn()==Bike && Rider->GetActorLocation().Equals(Seated,.1f));
    NewObstacle->Destroy();
    Bike->Dismount(); AdvanceExit();
    TestTrue(TEXT("Exit can retry after obstruction is removed"),Bike->CurrentRider==nullptr && Controller->GetPawn()==Rider);
    Bike->Mount(Rider,true);
    AActor* LeftSideBlock=Box(FVector(40,-120,200),FVector(5,5,200));
    AActor* RightSideBlock=Box(FVector(40,120,200),FVector(5,5,200));
    Bike->Dismount();
    TestTrue(TEXT("Blocked side exits select the rear-left dismount animation"),Bike->bDismounting
        && Rider->GetMesh()->GetAnimInstance()->Montage_IsPlaying(Rider->DismountLeftMontage));
    AdvanceExit(true);
    TestTrue(TEXT("Rear-side fallback restores the rider on the checked floor"),Bike->CurrentRider==nullptr
        && Controller->GetPawn()==Rider && Rider->GetActorLocation().X<-60.f && Rider->GetActorLocation().Y<-100.f
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);
    LeftSideBlock->Destroy(); RightSideBlock->Destroy();
    ReturnToLeftApproach();
    AActor* LeftWall=Box(FVector(0,-80,200),FVector(200,10,200));
    Rider->SetActorLocation(FVector(0,60,98.195294));
    Bike->Mount(Rider,false); Bike->Dismount();
    TestTrue(TEXT("Right exit plays matching animation"),Rider->GetMesh()->GetAnimInstance()->Montage_IsPlaying(Rider->DismountRightMontage));
    AdvanceExit(true);
    TestTrue(TEXT("Blocked left exit selects right side"),Bike->CurrentRider==nullptr && Rider->GetActorLocation().Y>100.f);
	LeftWall->Destroy();
	ReturnToLeftApproach();
	Bike->Mount(Rider,true);
	AActor* LeftExitWall=Box(FVector(0,-80,200),FVector(200,10,200));
    AActor* RightWall=Box(FVector(0,80,200),FVector(200,10,200));
    const FVector MountedLocation=Rider->GetActorLocation();
    Bike->Dismount();
    TestTrue(TEXT("Blocked exits keep rider mounted and possessed"),Bike->CurrentRider==Rider && Controller->GetPawn()==Bike
        && Rider->GetActorLocation().Equals(MountedLocation,.1f));
	LeftExitWall->SetActorLocation(FVector(0,-65,200));
	LeftExitWall->FindComponentByClass<UBoxComponent>()->SetBoxExtent(FVector(200,2,200));
	Bike->Dismount();
	TestTrue(TEXT("Clear destination beyond a wall is not a valid exit"),Bike->CurrentRider==Rider);
	LeftExitWall->Destroy(); RightWall->Destroy();
	Floor->SetActorRotation(FRotator(0.f,0.f,10.f));
	Bike->Dismount();
	TestTrue(TEXT("Ten-degree slope selects the downhill fitted dismount"),Bike->bDismounting
		&& Rider->GetMesh()->GetAnimInstance()->Montage_IsPlaying(Rider->DismountRightMontage));
	AdvanceExit(true);
	TestTrue(TEXT("Slope dismount restores the rider and walking collision"),Bike->CurrentRider==nullptr
		&& Controller->GetPawn()==Rider
		&& Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);
	Floor->SetActorRotation(FRotator::ZeroRotator);
	ReturnToLeftApproach();
	Bike->Mount(Rider,true);
	Floor->Destroy();
    Bike->Dismount();
    TestTrue(TEXT("Unsupported exits keep rider mounted"),Bike->CurrentRider==Rider && Controller->GetPawn()==Bike);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleMountRecoveryTest, "Carnival.Motorcycle.MountRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleMountRecoveryTest::RunTest(const FString&)
{
    UClass* BikeClass=LoadClass<ACarnivalMotorcycle>(nullptr,TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    UClass* RiderClass=LoadClass<ACarnivalPlayerCharacter>(nullptr,TEXT("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C"));
    if (!BikeClass || !RiderClass) { AddError(TEXT("Saved bike and rider required")); return false; }
    UGameInstance* Instance=NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleMountRecovery"));
    UWorld* World=Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto Box=[&](FVector Location,FVector Extent)
    {
        auto* Actor=World->SpawnActor<AActor>();
        auto* Component=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component); Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll")); Component->RegisterComponent();
        Actor->SetActorLocation(Location); return Actor;
    };
    AActor* Floor=Box(FVector(0,0,-20),FVector(1500,1500,20));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Controller=World->SpawnActor<APlayerController>();
    auto* Bike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    auto* Rider=World->SpawnActor<ACarnivalPlayerCharacter>(RiderClass,FVector(30,-60,98.195294),FRotator::ZeroRotator,Spawn);
    Controller->Possess(Rider);

    bool bMountLeft=false;
    TestTrue(TEXT("Offset left approach remains mountable"),Bike->CanMount(Rider,bMountLeft));
    TestTrue(TEXT("Left approach is selected"),bMountLeft);
    Bike->Mount(Rider,bMountLeft);
    TestTrue(TEXT("Left mount transfers possession and disables rider collision"),Bike->CurrentRider==Rider
        && Controller->GetPawn()==Bike && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
    Bike->Destroy();
    TestTrue(TEXT("Bike destruction restores rider possession, collision, and walking"),Controller->GetPawn()==Rider
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics
        && Rider->GetCharacterMovement()->MovementMode==MOVE_Walking);

    auto* RightBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    Rider->SetActorLocationAndRotation(FVector(0,60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    AActor* MountBlock=Box(FVector(0,60,98.195294),FVector(20,20,30));
    TestFalse(TEXT("Blocked approach does not offer a mount"),RightBike->CanMount(Rider,bMountLeft));
    RightBike->Mount(Rider,false);
    TestTrue(TEXT("Blocked approach leaves possession and rider collision intact"),RightBike->CurrentRider==nullptr
        && Controller->GetPawn()==Rider && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);
    MountBlock->Destroy();

    // A regular standing capsule cannot clear a path-only blocker within the
    // production 75 cm approach radius. Widen this fixture's range so both
    // capsule endpoints can be clear while the swept path crosses an obstacle.
    RightBike->MountApproachRadius=150.f;
    Rider->SetActorLocationAndRotation(FVector(-140,-60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    AActor* PathBlock=Box(FVector(-75,-60,98.195294),FVector(5,10,60));
    float RiderRadius=0.f, RiderHalfHeight=0.f;
    Rider->GetCapsuleComponent()->GetScaledCapsuleSize(RiderRadius,RiderHalfHeight);
    const FCollisionShape RiderCapsule=FCollisionShape::MakeCapsule(RiderRadius,RiderHalfHeight);
    FCollisionQueryParams PathParams(SCENE_QUERY_STAT(MotorcycleMountPathTest),false,RightBike);
    PathParams.AddIgnoredActor(Rider);
    const FVector LeftApproachEndpoint(0,-60,98.195294);
    TestFalse(TEXT("Path blocker does not overlap rider start"),World->OverlapBlockingTestByProfile(
        Rider->GetActorLocation(),FQuat::Identity,TEXT("Pawn"),RiderCapsule,PathParams));
    TestFalse(TEXT("Path blocker does not overlap mount endpoint"),World->OverlapBlockingTestByProfile(
        LeftApproachEndpoint,FQuat::Identity,TEXT("Pawn"),RiderCapsule,PathParams));
    FHitResult PathHit;
    TestTrue(TEXT("Path blocker intersects the approach sweep"),World->SweepSingleByProfile(PathHit,
        Rider->GetActorLocation(),LeftApproachEndpoint,FRotator::ZeroRotator.Quaternion(),TEXT("Pawn"),RiderCapsule,PathParams)
        && PathHit.GetActor()==PathBlock);
    TestFalse(TEXT("Blocked path rejects the mount when both endpoints are clear"),RightBike->CanMount(Rider,bMountLeft));
    PathBlock->Destroy();
    RightBike->MountApproachRadius=75.f;

    Rider->SetActorLocationAndRotation(FVector(300,-60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    TestFalse(TEXT("Out-of-range left approach is rejected"),RightBike->CanMount(Rider,bMountLeft));
    Rider->SetActorLocationAndRotation(FVector(300,60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    TestFalse(TEXT("Out-of-range right approach is rejected"),RightBike->CanMount(Rider,bMountLeft));
    RightBike->Mount(Rider,false);
    TestTrue(TEXT("Out-of-range direct mount leaves the rider on foot"),RightBike->CurrentRider==nullptr && Controller->GetPawn()==Rider);

    Rider->SetActorLocationAndRotation(FVector(-25,60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    TestTrue(TEXT("Offset right approach remains mountable"),RightBike->CanMount(Rider,bMountLeft));
    TestFalse(TEXT("Right approach is selected"),bMountLeft);
    RightBike->Mount(Rider,bMountLeft);
    TestTrue(TEXT("Right mount transfers possession and disables rider collision"),RightBike->CurrentRider==Rider
        && Controller->GetPawn()==RightBike && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);

	Controller->UnPossess();
    // Possession loss schedules emergency ejection for the next world tick
    // so APawn::UnPossessed can finish its controller transition first.
    World->Tick(LEVELTICK_All, 1.f/60.f);
    TestTrue(TEXT("Unexpected controller loss restores rider possession, collision, and movement"),RightBike->CurrentRider==nullptr
        && Controller->GetPawn()==Rider && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics
        && Rider->GetCharacterMovement()->MovementMode==MOVE_Walking);
    RightBike->Destroy();

    auto* RecoveryBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    Rider->SetActorLocationAndRotation(FVector(0,-60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    Controller->Possess(Rider);
    RecoveryBike->Mount(Rider,true);
    AActor* RecoveryWall=Box(FVector(75,0,100),FVector(10,220,120));
    RecoveryBike->InputThrottle(1.f);
    for (int32 I=0; I<300; ++I)
    {
        ++GFrameCounter;
        Rider->GetMesh()->TickAnimation(1.f/60.f,false);
        Rider->GetMesh()->RefreshBoneTransforms();
        Rider->Tick(1.f/60.f);
        RecoveryBike->Tick(1.f/60.f);
    }
    RecoveryBike->Dismount();
    TestTrue(TEXT("Stuck recovery moves to clear ground and preserves mounted control"),RecoveryBike->GetActorLocation().X<-50.f
        && RecoveryBike->CurrentSpeed==0.f && RecoveryBike->CurrentRider==Rider && Controller->GetPawn()==RecoveryBike
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
    RecoveryWall->Destroy();
	const FVector BeforeDriveResume=RecoveryBike->GetActorLocation();
	RecoveryBike->InputThrottle(1.f);
	for (int32 I=0; I<30; ++I) RecoveryBike->Tick(1.f/60.f);
	TestTrue(TEXT("Rider can drive again after recovery"),RecoveryBike->CurrentSpeed>0.f
		&& FVector::Dist(RecoveryBike->GetActorLocation(),BeforeDriveResume)>1.f
		&& Controller->GetPawn()==RecoveryBike);
	RecoveryBike->InputThrottle(0.f);
	RecoveryBike->CurrentSpeed=0.f;

    RecoveryBike->SetActorRotation(FRotator(180.f,0.f,0.f));
    RecoveryBike->Dismount();
    TestTrue(TEXT("Overturn recovery restores upright driving while keeping rider possession"),RecoveryBike->GetActorUpVector().Z>.99f
        && RecoveryBike->CurrentRider==Rider && Controller->GetPawn()==RecoveryBike
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);

    RecoveryBike->Destroy();

    auto* ParkedOverturnedBike=World->SpawnActor<ACarnivalMotorcycle>(BikeClass,FVector(500,0,0),FRotator(180.f,0.f,0.f),Spawn);
    Rider->SetActorLocationAndRotation(FVector(500,-200,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    Controller->Possess(Rider);
    TestTrue(TEXT("On-foot player can identify an overturned nearby motorcycle"),ParkedOverturnedBike->CanRecoverFromStuckOrOverturned());
    Rider->TryInteractOrMount();
    TestTrue(TEXT("Vehicle action rights an overturned parked bike without mounting or losing walking control"),
        ParkedOverturnedBike->GetActorUpVector().Z>.99f && ParkedOverturnedBike->CurrentRider==nullptr
        && Controller->GetPawn()==Rider
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics
        && Rider->GetCharacterMovement()->MovementMode==MOVE_Walking);
    Rider->SetActorLocationAndRotation(FVector(500,-60,98.195294),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
    Rider->TryInteractOrMount();
    TestTrue(TEXT("Next vehicle action can mount the recovered motorcycle"),ParkedOverturnedBike->CurrentRider==Rider
        && Controller->GetPawn()==ParkedOverturnedBike
        && Rider->GetCapsuleComponent()->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
    ParkedOverturnedBike->Destroy();
    Floor->Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMotorcycleRiderPlaybackTest, "Carnival.Motorcycle.RiderPlayback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMotorcycleRiderPlaybackTest::RunTest(const FString&)
{
    UClass* BikeClass = LoadClass<ACarnivalMotorcycle>(nullptr,
        TEXT("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C"));
    UClass* RiderClass = LoadClass<ACarnivalPlayerCharacter>(nullptr,
        TEXT("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C"));
    if (!BikeClass || !RiderClass) { AddError(TEXT("Saved bike and rider classes required")); return false; }
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("MotorcycleRiderPlayback"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto* Floor=World->SpawnActor<AActor>();
    auto* FloorBox=NewObject<UBoxComponent>(Floor);
    Floor->SetRootComponent(FloorBox); FloorBox->SetBoxExtent(FVector(1000,1000,20));
    FloorBox->SetCollisionProfileName(TEXT("BlockAll")); FloorBox->RegisterComponent();
    Floor->SetActorLocation(FVector(0,0,-20));
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>(BikeClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    auto* Rider = World->SpawnActor<ACarnivalPlayerCharacter>(RiderClass, FVector(0,-60,98.195294), FRotator::ZeroRotator, Spawn);
    bool bMountSide=false;
    Bike->CurrentSpeed=100.f;
    TestFalse(TEXT("Moving bike does not offer a mount"),Bike->CanMount(Rider,bMountSide));
    Bike->Mount(Rider,true);
    TestNull(TEXT("Direct mount also rejects a moving bike"),Bike->CurrentRider);
    Bike->CurrentSpeed=0.f; Bike->bIsAirborne=true;
    TestFalse(TEXT("Airborne bike does not offer a mount"),Bike->CanMount(Rider,bMountSide));
    Bike->Mount(Rider,true);
    TestNull(TEXT("Direct mount also rejects an airborne bike"),Bike->CurrentRider);
    Bike->bIsAirborne=false;
    Bike->Mount(Rider, true);
    TestTrue(TEXT("Mounted capsule follows real seat socket"), Rider->GetActorLocation().Equals(
        Bike->BikeMesh->GetSocketLocation(Bike->DriverSeatSocketName), .1f));
    UAnimInstance* Anim = Rider->GetMesh()->GetAnimInstance();
    if (!TestNotNull(TEXT("Saved rider anim instance initialized"), Anim)) return false;
    for (bool bLeft : {true,false})
    {
        Rider->OnMountMotorcycle(Bike,bLeft);
        const UAnimMontage* Selected=bLeft ? Rider->MountLeftMontage : Rider->MountRightMontage;
        TestTrue(TEXT("Saved player uses fitted mount"),Selected && Selected->GetName().Contains(TEXT("Fitted_Mount")));
        float MaxSeatedPelvisError=0.f;
        for (int32 I=0; I<150; ++I)
        {
            ++GFrameCounter;
            Rider->GetMesh()->TickAnimation(1.f/60.f,false);
            Rider->GetMesh()->RefreshBoneTransforms();
            Rider->Tick(1.f/60.f);
            if (I==39)
            {
                const FVector NearFoot=Rider->GetMesh()->GetBoneLocation(bLeft ? TEXT("foot_l") : TEXT("foot_r"));
                const FVector FarFoot=Rider->GetMesh()->GetBoneLocation(bLeft ? TEXT("foot_r") : TEXT("foot_l"));
                AddInfo(FString::Printf(TEXT("%s runtime mount midpoint feet %s / %s"),bLeft ? TEXT("Left") : TEXT("Right"),*NearFoot.ToString(),*FarFoot.ToString()));
                TestTrue(TEXT("Runtime mount plants near foot at peg height"),FMath::Abs(NearFoot.Z-46.f)<2.f);
                TestTrue(TEXT("Runtime mount crossing foot clears seat height"),FarFoot.Z>110.f);
                const FVector BeforeDrive=Bike->GetActorLocation();
                const float BeforeYaw=Bike->GetActorRotation().Yaw;
                Bike->InputThrottle(1.f); Bike->InputSteering(1.f); Bike->InputRiderBalance(1.f);
                Bike->Tick(1.f/60.f);
                TestTrue(TEXT("Held driving controls cannot move bike during step-over"),
                    FMath::IsNearlyZero(Bike->CurrentSpeed) && Bike->GetActorLocation().Equals(BeforeDrive,.1f)
                    && FMath::IsNearlyEqual(Bike->GetActorRotation().Yaw,BeforeYaw,.01f));
                Bike->InputThrottle(0.f); Bike->InputSteering(0.f); Bike->InputRiderBalance(0.f);
            }
            if (I>=84)
                MaxSeatedPelvisError=FMath::Max(MaxSeatedPelvisError,float(FVector::Distance(
                    Rider->GetMesh()->GetBoneLocation(TEXT("pelvis")),FVector(-8.719,0,92.092))));
        }
        TestTrue(TEXT("Mount hands off to looping riding idle"),Anim->Montage_IsPlaying(Rider->RidingIdleMontage));
        AddInfo(FString::Printf(TEXT("%s maximum seated handoff pelvis error %.3f cm"),bLeft ? TEXT("Left") : TEXT("Right"),MaxSeatedPelvisError));
        TestTrue(TEXT("Mount-to-idle does not dip into standing locomotion"),MaxSeatedPelvisError<2.f);
        TestTrue(TEXT("Mount-to-idle retains both peg contacts"),
            Rider->GetMesh()->GetBoneLocation(TEXT("foot_l")).Equals(FVector(-8,-25,46),1.f)
            && Rider->GetMesh()->GetBoneLocation(TEXT("foot_r")).Equals(FVector(-8,25,46),1.f));
        Bike->InputThrottle(1.f); Bike->Tick(1.f/60.f);
        TestTrue(TEXT("Driving resumes when mount hands off to riding idle"),Bike->CurrentSpeed>0.f);
        Bike->InputThrottle(0.f); Bike->CurrentSpeed=0.f;
        Bike->SetActorLocation(FVector::ZeroVector);
    }
    for (UAnimMontage* Montage : {Rider->MountLeftMontage, Rider->MountRightMontage,
        Rider->RidingIdleMontage, Rider->DismountLeftMontage, Rider->DismountRightMontage})
    {
        if (!TestNotNull(TEXT("Mounted animation assigned"), Montage)) continue;
        Anim->Montage_Stop(0.f);
        const float Length = Anim->Montage_Play(Montage);
        AddInfo(FString::Printf(TEXT("%s playback length %.3f"), *GetNameSafe(Montage), Length));
        TestTrue(TEXT("Saved mounted clip can play on rider skeleton"), Length > 0.f);
    }
    Anim->Montage_Stop(0.f);
    Rider->Tick(0.f); // Exercise the gameplay idle start and section loop.
    for (int32 I=0; I<45; ++I)
    {
        ++GFrameCounter;
        Rider->GetMesh()->TickAnimation(1.f/60.f, false);
        Rider->GetMesh()->RefreshBoneTransforms();
    }
    const FVector Pelvis = Rider->GetMesh()->GetBoneLocation(TEXT("pelvis"));
    const FVector LeftFoot = Rider->GetMesh()->GetBoneLocation(TEXT("foot_l"));
    const FVector RightFoot = Rider->GetMesh()->GetBoneLocation(TEXT("foot_r"));
    AddInfo(FString::Printf(TEXT("Mounted mesh location %s, actor %s, IK curve %.3f"),
        *Rider->GetMesh()->GetComponentLocation().ToString(), *Rider->GetActorLocation().ToString(),
        Anim->GetCurveValue(TEXT("DisableLegIK"))));
    AddInfo(TEXT("Rider animation class: ") + Anim->GetClass()->GetPathName());
    for (TFieldIterator<FStructProperty> It(Anim->GetClass()); It; ++It)
    {
        if (It->Struct->GetFName() != TEXT("AnimNode_ControlRig")) continue;
        void* Data=It->ContainerPtrToValuePtr<void>(Anim);
        for (FName Name : {FName(TEXT("AlphaInputType")),FName(TEXT("AlphaCurveName")),FName(TEXT("AlphaScaleBiasClamp"))})
        {
            FProperty* Property=It->Struct->FindPropertyByName(Name);
            FString Value;
            if (Property) Property->ExportText_InContainer(0,Value,Data,Data,nullptr,PPF_None);
            AddInfo(Name.ToString()+TEXT(": ")+Value);
        }
    }
    AddInfo(FString::Printf(TEXT("Mounted evaluated pelvis %s, feet %s / %s"),
        *Pelvis.ToString(), *LeftFoot.ToString(), *RightFoot.ToString()));
    AddInfo(FString::Printf(TEXT("Mounted evaluated hands %s / %s"),
        *Rider->GetMesh()->GetBoneLocation(TEXT("hand_l")).ToString(),
        *Rider->GetMesh()->GetBoneLocation(TEXT("hand_r")).ToString()));
    TestTrue(TEXT("Riding montage actually lifts both feet into seated pose"),
        LeftFoot.Z > 20.f && LeftFoot.Z < 75.f && RightFoot.Z > 20.f && RightFoot.Z < 75.f);
    TestTrue(TEXT("Riding legs retain authored peg placement through the animation graph"),
        LeftFoot.Equals(FVector(-8,-25,46), 1.f) && RightFoot.Equals(FVector(-8,25,46), 1.f));
    TestTrue(TEXT("Riding hands retain authored grip placement through the animation graph"),
        Rider->GetMesh()->GetBoneLocation(TEXT("hand_l")).Equals(FVector(34,-39,128), 1.f)
        && Rider->GetMesh()->GetBoneLocation(TEXT("hand_r")).Equals(FVector(34,39,128), 1.f));
    for (int32 I=0; I<240; ++I) { ++GFrameCounter; Rider->GetMesh()->TickAnimation(1.f/60.f,false); Rider->GetMesh()->RefreshBoneTransforms(); }
    TestTrue(TEXT("Gameplay riding idle remains active across several loops"),Anim->Montage_IsPlaying(Rider->RidingIdleMontage));
    TestTrue(TEXT("Looping idle retains foot contact"),Rider->GetMesh()->GetBoneLocation(TEXT("foot_l")).Equals(FVector(-8,-25,46),1.f));
    return true;
}
#endif
