#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalRideAttendant.h"
#include "CarnivalRideControllerComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "CarnivalRideQueueComponent.h"
#include "CarnivalQueuePoint.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalMotorcycle.h"
#include "EnhancedPlayerInput.h"
#include "EnhancedInputSubsystemInterface.h"
#include "InputMappingContext.h"
#include "InputKeyEventArgs.h"
#include "Components/BoxComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAttendedSwingTest, "Carnival.Rides.AttendedSwing",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAttendedSwingTest::RunTest(const FString&)
{
    UClass* RideClass = LoadClass<AActor>(nullptr, TEXT("/Game/Carnival/Rides/BP_Swing_Carnival.BP_Swing_Carnival_C"));
    if (!TestNotNull(TEXT("Swing ride asset loads"), RideClass)) return false;
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("RideAutomation"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL;
    URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL);
    World->InitializeActorsForPlay(URL);
    World->BeginPlay();
    AActor* Floor = World->SpawnActor<AActor>();
    UBoxComponent* Box = NewObject<UBoxComponent>(Floor);
    Floor->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(5000,5000,20));
    Box->SetCollisionProfileName(TEXT("BlockAll"));
    Box->RegisterComponent();
    Floor->SetActorLocation(FVector(0,0,-20));
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AActor* Ride = World->SpawnActor<AActor>(RideClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    auto* Staff = World->SpawnActor<ACarnivalRideAttendant>(FVector(2200,0,91), FRotator::ZeroRotator, Spawn);
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(2400,0,98), FRotator::ZeroRotator, Spawn);
    Player->GetCharacterMovement()->bRunPhysicsWithNoController = true;
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Attendant accepts ride"), Staff->AssignRide(Ride));
    auto* Operation = Staff->Operation.Get();
    auto* Controller = Ride->FindComponentByClass<UCarnivalRideControllerComponent>();
    if (!TestNotNull(TEXT("Operation created"), Operation) || !TestNotNull(TEXT("Ride controller exists"), Controller)) return false;
    Operation->BoardingSeconds = .25f;
    Operation->SecuringSeconds = .25f;
    Operation->CycleSeconds = 30.f;
    Operation->ReturnSeconds = .6f;
    Operation->UnloadingSeconds = .2f;
    auto Step = [&](float Seconds)
    {
        for (int32 I=0; I<FMath::CeilToInt(Seconds*60); ++I)
        { ++GFrameCounter; World->Tick(LEVELTICK_All, 1.f/60.f); }
    };
    Step(.3f);
    TestTrue(TEXT("Vendor start and stop functions configured"), Operation->IsReady());
    TestEqual(TEXT("Attendant opens boarding"), Operation->State, ECarnivalOperationState::Loading);
    TestEqual(TEXT("Swing has all authored seats"), Controller->GetSeats().Num(), 34);
    const FTransform Entry = Player->GetActorTransform();
    const EMovementMode EntryMode = Player->GetCharacterMovement()->MovementMode;
    TestTrue(TEXT("Nearby player boards"), Operation->RequestBoard(Player));
    auto* Seat = Player->RidePassenger->GetCurrentSeat();
    if (!TestNotNull(TEXT("Player assigned a seat"), Seat)) return false;
    const FTransform Home = Seat->GetComponentTransform();
    TestFalse(TEXT("Cannot board same passenger twice"), Operation->RequestBoard(Player));
    TestFalse(TEXT("Seated player cannot take operator controls"), Operation->TakeOperatorControl(Player));
    TestEqual(TEXT("Boarding disables walking physics"), Player->GetCharacterMovement()->MovementMode.GetValue(), MOVE_None);
    TestFalse(TEXT("Boarding disables character collision"), Player->GetActorEnableCollision());
    Step(.7f);
    TestEqual(TEXT("Attendant starts the cycle"), Operation->State, ECarnivalOperationState::Running);
    float MaxSeatTravel = 0.f, MaxAttachmentError = 0.f;
    for (int32 I=0; I<600; ++I)
    {
        Step(1.f/60.f);
        MaxSeatTravel = FMath::Max(MaxSeatTravel, static_cast<float>(FVector::Distance(Home.GetLocation(), Seat->GetComponentLocation())));
        MaxAttachmentError = FMath::Max(MaxAttachmentError, static_cast<float>(FVector::Distance(Player->GetActorLocation(), Seat->GetPassengerWorldTransform().GetLocation())));
    }
    TestTrue(TEXT("Vendor ride physically moves occupied seat"), MaxSeatTravel > 100.f);
    TestTrue(TEXT("Character stays attached to moving seat"), MaxAttachmentError < 1.f);
    auto* Other = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(2400,150,98), FRotator::ZeroRotator, Spawn);
    TestFalse(TEXT("Cannot board a moving ride"), Operation->RequestBoard(Other));
    TestTrue(TEXT("Exit request accepted"), Operation->RequestPassengerExit(Player));
    TestTrue(TEXT("Passenger stays seated during return"), Player->RidePassenger->IsRiding());
    TestEqual(TEXT("Exit triggers controlled return"), Operation->State, ECarnivalOperationState::Returning);
    Step(.65f);
    TestTrue(TEXT("Seat returns to loading pose"), Seat->GetComponentTransform().Equals(Home, .05f));
    TestFalse(TEXT("Passenger released at platform"), Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Collision restored after unloading"), Player->GetActorEnableCollision());
    TestFalse(TEXT("Movement restored after unloading"), Player->GetCharacterMovement()->MovementMode == MOVE_None);
    AddInfo(FString::Printf(TEXT("Player movement at entry=%d; after exit=%d; entry height=%.2f; exit height=%.2f"), EntryMode,
        Player->GetCharacterMovement()->MovementMode.GetValue(), Entry.GetLocation().Z, Player->GetActorLocation().Z));
    TestTrue(TEXT("Passenger returns to boarding position"), FVector::Distance(Player->GetActorLocation(), Entry.GetLocation()) < 5.f);
    TestFalse(TEXT("Seat freed after unloading"), Seat->IsOccupied());
    Step(.3f);
    TestTrue(TEXT("Player can take controls"), Operation->TakeOperatorControl(Player));
    TestTrue(TEXT("Reassigning same attendant is idempotent"), Staff->AssignRide(Ride));
    TestEqual(TEXT("Idempotent assignment retains player control"), Operation->PlayerOperator.Get(), static_cast<AActor*>(Player));
    TestFalse(TEXT("Another player cannot also operate"), Operation->TakeOperatorControl(Other));
    TestFalse(TEXT("Non-operator cannot start"), Operation->OperatorStart(Other));
    TestTrue(TEXT("Operator starts empty ride"), Operation->OperatorStart(Player));
    Step(.4f);
    Operation->ReleaseOperatorControl(Player);
    TestEqual(TEXT("Handover preserves running cycle"), Operation->State, ECarnivalOperationState::Running);
    Operation->CycleSeconds = 1.f;
    Step(2.f);
    TestEqual(TEXT("Attendant completes handed-back cycle"), Operation->State, ECarnivalOperationState::Loading);
    TestTrue(TEXT("Ride supports another boarding cycle"), Operation->RequestBoard(Player));
    Step(.7f);
    Staff->Destroy();
    Step(1.f);
    TestFalse(TEXT("Attendant loss safely unloads player"), Player->RidePassenger->IsRiding());
    TestEqual(TEXT("Unstaffed ride closes"), Operation->State, ECarnivalOperationState::Closed);
    TestFalse(TEXT("Unstaffed ride rejects boarding"), Operation->RequestBoard(Player));
    auto* Replacement = World->SpawnActor<ACarnivalRideAttendant>(FVector(2200,0,91), FRotator::ZeroRotator, Spawn);
    TestTrue(TEXT("Replacement staff can reopen ride"), Replacement->AssignRide(Ride));
    Step(.1f);
    TestEqual(TEXT("Replacement staff reopens boarding"), Operation->State, ECarnivalOperationState::Loading);
    TestTrue(TEXT("Replacement staff permits operator handover"), Operation->TakeOperatorControl(Player));
    Player->SetActorLocation(FVector(4000,0,98));
    Step(.1f);
    TestNull(TEXT("Leaving controls hands operation back to staff"), Operation->PlayerOperator.Get());
    Player->SetActorLocation(Entry.GetLocation());
    TestTrue(TEXT("Returned player can take operator control"), Operation->TakeOperatorControl(Player));
    Replacement->Destroy();
    TestNull(TEXT("Staff destruction releases operator immediately"), Operation->PlayerOperator.Get());
    Step(.1f);
    Replacement = World->SpawnActor<ACarnivalRideAttendant>(FVector(2200,0,91), FRotator::ZeroRotator, Spawn);
    Replacement->Experience = ECarnivalRideExperience::Show;
    Replacement->AssignRide(Ride);
    Step(.1f);
    TestTrue(TEXT("Visitor can request an attended show"), Operation->RequestBoard(Player));
    TestFalse(TEXT("Show visitors are not attached to seats"), Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Show visitors retain collision"), Player->GetActorEnableCollision());
    TestFalse(TEXT("Show visitors retain movement"), Player->GetCharacterMovement()->MovementMode == MOVE_None);
    TestEqual(TEXT("Show request enters timed cycle"), Operation->State, ECarnivalOperationState::Securing);
    AddInfo(FString::Printf(TEXT("Swing metrics: max seat travel %.2f cm; max passenger attachment error %.4f cm; completed cycles %d"), MaxSeatTravel, MaxAttachmentError, Operation->CompletedCycles));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRideQueueRecoveryTest, "Carnival.Rides.QueueRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRideQueueRecoveryTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("RideQueueRecovery"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto* FirstPoint = World->SpawnActor<ACarnivalQueuePoint>();
    auto* SecondPoint = World->SpawnActor<ACarnivalQueuePoint>();
    FirstPoint->RideId = SecondPoint->RideId = TEXT("QueueRecovery");
    FirstPoint->QueueIndex = 0; SecondPoint->QueueIndex = 1;
    FirstPoint->SetActorLocation(FVector(100,0,0));
    SecondPoint->SetActorLocation(FVector(200,0,0));
    auto* Owner = World->SpawnActor<AActor>();
    auto* Queue = NewObject<UCarnivalRideQueueComponent>(Owner);
    Queue->RideId = TEXT("QueueRecovery"); Queue->RegisterComponent(); Queue->DiscoverQueuePoints();
    auto* First = World->SpawnActor<AActor>();
    auto* Second = World->SpawnActor<AActor>();
    auto* Third = World->SpawnActor<AActor>();
    TestTrue(TEXT("First guest enters queue"), Queue->EnqueueGuest(First));
    TestFalse(TEXT("Duplicate guest is rejected"), Queue->EnqueueGuest(First));
    TestTrue(TEXT("Second guest fills queue"), Queue->EnqueueGuest(Second));
    TestFalse(TEXT("Full queue rejects extra guest"), Queue->EnqueueGuest(Third));
    First->Destroy();
    TestEqual(TEXT("Destroyed guest frees capacity immediately"), Queue->GetQueueLength(), 1);
    TestTrue(TEXT("Surviving guest advances past destroyed guest"), Queue->GetGuestQueueTarget(Second).Equals(FirstPoint->GetActorTransform()));
    TestTrue(TEXT("New guest can use freed slot"), Queue->EnqueueGuest(Third));
    FirstPoint->Destroy();
    TestEqual(TEXT("Destroyed marker reduces queue capacity"), Queue->GetQueueCapacity(), 1);
    TestTrue(TEXT("Queue target skips destroyed marker"), Queue->GetGuestQueueTarget(Second).Equals(SecondPoint->GetActorTransform()));
    TestEqual(TEXT("Dequeue retains FIFO order"), Queue->PopNextGuest(), Second);
    TestEqual(TEXT("Final guest can leave"), Queue->PopNextGuest(), Third);
    TestEqual(TEXT("Queue finishes empty"), Queue->GetQueueLength(), 0);

    auto* Operation = NewObject<UCarnivalRideOperationComponent>(Owner);
    Operation->RegisterComponent();
    TestFalse(TEXT("Missing controller rejects initialization"), Operation->InitializeOperation());
    auto* Controller = NewObject<UCarnivalRideControllerComponent>(Owner);
    Controller->RegisterComponent();
    TestFalse(TEXT("Seatless controller is not a ready ride"), Operation->InitializeOperation());
    TestTrue(TEXT("Retry reports current seat configuration failure"), Operation->ConfigurationError.Contains(TEXT("No passenger seats")));
    TestFalse(TEXT("Invalid attended ride cannot reopen via motion telemetry"), Controller->bAutoDetectPhase);
    TestEqual(TEXT("Invalid attended ride holds boarding closed"), Controller->RidePhase, ECarnivalRidePhase::Closed);
    Operation->DestroyComponent();
    TestTrue(TEXT("Removing attended operation restores phase detection"), Controller->bAutoDetectPhase);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRidePassengerRecoveryTest, "Carnival.Rides.PassengerRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRidePassengerRecoveryTest::RunTest(const FString&)
{
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("RideRecovery"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL;
    URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    AActor* Ride = World->SpawnActor<AActor>();
    auto* Seat = NewObject<UCarnivalRideSeatComponent>(Ride);
    Ride->SetRootComponent(Seat); Seat->RegisterComponent();
    Seat->SetWorldLocation(FVector(500,0,200));
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>();
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    Player->SetActorEnableCollision(false);
    const FTransform Entry = Player->GetActorTransform();
    TestFalse(TEXT("Foreign ride cannot claim seat"), Player->RidePassenger->BoardRide(Player, Seat));
    TestTrue(TEXT("Recovery fixture boards"), Player->RidePassenger->BoardRide(Ride, Seat));
    Ride->Destroy();
    ++GFrameCounter; World->Tick(LEVELTICK_All, 1.f/60.f);
    TestFalse(TEXT("Destroyed ride releases passenger"), Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Destroyed ride restores entry position"), Player->GetActorTransform().Equals(Entry, .01f));
    TestEqual(TEXT("Original non-walking mode restored"), Player->GetCharacterMovement()->MovementMode.GetValue(), MOVE_Flying);
    TestFalse(TEXT("Original disabled collision restored"), Player->GetActorEnableCollision());
    Ride = World->SpawnActor<AActor>();
    Seat = NewObject<UCarnivalRideSeatComponent>(Ride);
    Ride->SetRootComponent(Seat); Seat->RegisterComponent();
    Player->RidePassenger->BoardRide(Ride, Seat);
    Player->Destroy();
    TestFalse(TEXT("Destroyed passenger releases seat immediately"), Seat->IsOccupied());
    return true;
}

// Use the engine's real key mapping, modifiers, triggers and action delegates.
// This substitutes only the local-player subsystem for a headless test world.
class FRideTestInputSubsystem : public IEnhancedInputSubsystemInterface
{
public:
    UEnhancedPlayerInput* Input = nullptr;
    TMap<TObjectPtr<const UInputAction>, FInjectedInput> Injected;
    virtual UEnhancedPlayerInput* GetPlayerInput() const override { return Input; }
    virtual TMap<TObjectPtr<const UInputAction>, FInjectedInput>& GetContinuouslyInjectedInputs() override { return Injected; }
};

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRideInputTest, "Carnival.Rides.ControllerInput",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRideInputTest::RunTest(const FString&)
{
    UClass* PCClass = LoadClass<ACarnivalPlayerController>(nullptr, TEXT("/Game/Carnival/Blueprints/BP_CarnivalPlayerController.BP_CarnivalPlayerController_C"));
    UClass* RideClass = LoadClass<AActor>(nullptr, TEXT("/Game/Carnival/Rides/BP_Swing_Carnival.BP_Swing_Carnival_C"));
    if (!PCClass || !RideClass) { AddError(TEXT("Input and swing assets must be installed")); return false; }
    UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
    Instance->InitializeStandalone(TEXT("RideInput"));
    UWorld* World = Instance->GetWorld();
    ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
    FURL URL; URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
    World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
    auto* PC = World->SpawnActor<ACarnivalPlayerController>(PCClass);
    PC->InitInputSystem();
    auto* Input = Cast<UEnhancedPlayerInput>(PC->PlayerInput);
    if (!TestNotNull(TEXT("Enhanced input initialized"), Input)) return false;
    FRideTestInputSubsystem Subsystem;
    Subsystem.Input = Input;
    FModifyContextOptions Options; Options.bForceImmediately = true; Options.bIgnoreAllPressedKeysUntilRelease = false;
    Subsystem.AddMappingContext(PC->DefaultMappingContext, 0, Options);
    TestTrue(TEXT("Saved input context contains live mappings"), Input->GetEnhancedActionMappingsView().Num() > 20);
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(2200,0,100), FRotator::ZeroRotator, Spawn);
    PC->Possess(Player);
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    auto* Ride = World->SpawnActor<AActor>(RideClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    auto* Staff = World->SpawnActor<ACarnivalRideAttendant>(FVector(2300,0,100), FRotator::ZeroRotator, Spawn);
    Staff->AssignRide(Ride);
    auto* Operation = Staff->Operation.Get();
    Operation->InitializeOperation();
    Operation->SecuringSeconds = .1f;
    auto Key = [&](FKey KeyName, EInputEvent Event, float Value)
    { PC->InputKey(FInputKeyEventArgs::CreateSimulated(KeyName, Event, Value)); };
    auto Process = [&]() { Input->ProcessInputStack({PC->InputComponent}, 1.f/60.f, false); };
    Key(EKeys::Gamepad_LeftX, IE_Axis, .1f); Process();
    TestTrue(TEXT("Small stick drift is filtered"), Input->GetActionValue(PC->MoveAction).IsNonZero() == false);
    Key(EKeys::Gamepad_LeftX, IE_Axis, .6f); Process();
    const FVector2D Move = Input->GetActionValue(PC->MoveAction).Get<FVector2D>();
    TestTrue(TEXT("Left stick supports analog movement"), Move.X > .1 && Move.X < 1 && FMath::Abs(Move.Y) < .001);
    Key(EKeys::Gamepad_LeftX, IE_Axis, 0.f); Process();
    Player->ConsumeMovementInputVector();
    Key(EKeys::Gamepad_RightY, IE_Axis, .7f); Process();
    TestTrue(TEXT("Right stick has correct vertical direction"), Input->GetActionValue(PC->LookStickAction).Get<FVector2D>().Y < -.1);
    Key(EKeys::Gamepad_RightY, IE_Axis, 0.f); Process();
    auto Press = [&](FKey Button)
    { Key(Button, IE_Pressed, 1.f); Process(); Key(Button, IE_Released, 0.f); Process(); };
    Press(EKeys::Gamepad_FaceButton_Top);
    TestTrue(TEXT("Triangle boards through input dispatch"), Player->RidePassenger->IsRiding());
    TestTrue(TEXT("Controller activity selects controller prompts"), PC->bUsingGamepad);
    Press(EKeys::Gamepad_FaceButton_Left);
    TestFalse(TEXT("Square cannot jump out of seat"), Player->bPressedJump);
    Press(EKeys::Gamepad_FaceButton_Top);
    TestFalse(TEXT("Triangle exits at loading"), Player->RidePassenger->IsRiding());
    Press(EKeys::Gamepad_DPad_Right);
    TestEqual(TEXT("D-pad right takes operator controls"), Player->OperatingRide.Get(), Operation);
    Press(EKeys::Gamepad_FaceButton_Bottom);
    TestEqual(TEXT("Cross starts securing"), Operation->State, ECarnivalOperationState::Securing);
    for (int32 I=0; I<10; ++I) { ++GFrameCounter; World->Tick(LEVELTICK_All, 1.f/60.f); }
    Press(EKeys::Gamepad_FaceButton_Left);
    TestEqual(TEXT("Square requests platform return"), Operation->State, ECarnivalOperationState::Returning);
    Press(EKeys::Gamepad_FaceButton_Right);
    TestNull(TEXT("Circle returns controls to attendant"), Operation->PlayerOperator.Get());
    TestFalse(TEXT("Circle restores player movement"), Player->GetCharacterMovement()->MovementMode == MOVE_None);
    Press(EKeys::E);
    TestFalse(TEXT("Keyboard activity restores keyboard prompts"), PC->bUsingGamepad);
    Player->LeaveRideOperator();
    auto* Bike = World->SpawnActor<ACarnivalMotorcycle>(FVector(4000,0,100), FRotator::ZeroRotator, Spawn);
    PC->Possess(Bike);
    Subsystem.RemoveMappingContext(PC->DefaultMappingContext, Options);
    Subsystem.AddMappingContext(PC->MotorcycleMappingContext, 0, Options);
    Key(EKeys::Gamepad_RightTriggerAxis, IE_Axis, .8f); Process();
    TestTrue(TEXT("R2 gives analog throttle"), Input->GetActionValue(PC->ThrottleAction).Get<float>() > .5f);
    Bike->CurrentRider = Player;
    Bike->Tick(.1f);
    const float PoweredSpeed = Bike->CurrentSpeed;
    Key(EKeys::Gamepad_RightTriggerAxis, IE_Axis, 0.f); Process();
    Bike->Tick(.1f);
    TestTrue(TEXT("Released throttle no longer accelerates bike"), PoweredSpeed > 0.f && Bike->CurrentSpeed < PoweredSpeed);
    Key(EKeys::Gamepad_LeftX, IE_Axis, .8f); Process();
    Bike->CurrentSpeed = 300.f; Bike->Tick(.1f);
    Key(EKeys::Gamepad_LeftX, IE_Axis, 0.f); Process();
    const float ReleasedYaw = Bike->GetActorRotation().Yaw;
    Bike->Tick(.1f);
    TestTrue(TEXT("Released steering no longer turns bike"), FMath::IsNearlyEqual(Bike->GetActorRotation().Yaw, ReleasedYaw, .001f));
    Key(EKeys::Gamepad_LeftTriggerAxis, IE_Axis, .8f); Process();
    Bike->CurrentSpeed = 300.f; Bike->Tick(.05f);
    const float BrakedSpeed = Bike->CurrentSpeed;
    Key(EKeys::Gamepad_LeftTriggerAxis, IE_Axis, 0.f); Process();
    Bike->CurrentSpeed = 300.f; Bike->Tick(.05f);
    TestTrue(TEXT("Released brake restores normal coasting"), Bike->CurrentSpeed > BrakedSpeed);
    if (!TestNotNull(TEXT("L2 brake reverse action installed"), PC->BrakeReverseAction)) return false;
    auto* Ground = World->SpawnActor<AActor>();
    auto* GroundBox = NewObject<UBoxComponent>(Ground);
    Ground->SetRootComponent(GroundBox); GroundBox->SetBoxExtent(FVector(5000,5000,20));
    GroundBox->SetCollisionProfileName(TEXT("BlockAll")); GroundBox->RegisterComponent();
    Ground->SetActorLocation(FVector(10000,0,-20));
    Bike->SetActorLocation(FVector(10000,0,0)); Bike->SetActorRotation(FRotator::ZeroRotator);
    Bike->bIsAirborne=false; Bike->VerticalVelocity=0.f; Bike->CurrentSpeed=300.f;
    Key(EKeys::Gamepad_LeftTriggerAxis, IE_Axis, .8f); Process();
    bool bStoppedBeforeReverse=false;
    for (int32 I=0; I<120; ++I)
    {
        const float Before=Bike->CurrentSpeed;
        Bike->Tick(1.f/60.f);
        if (Before>=0.f && FMath::IsNearlyZero(Bike->CurrentSpeed)) bStoppedBeforeReverse=true;
        if (Bike->CurrentSpeed<0.f) TestTrue(TEXT("L2 passes through stop before reversing"),bStoppedBeforeReverse);
    }
    TestTrue(TEXT("Held L2 backs bike up with analog speed"),Bike->CurrentSpeed < -100.f && Bike->CurrentSpeed > -Bike->ReverseSpeed);
    Key(EKeys::Gamepad_RightTriggerAxis, IE_Axis, 1.f); Process();
    for (int32 I=0; I<60; ++I) Bike->Tick(1.f/60.f);
    TestTrue(TEXT("Opposing triggers stop and hold bike"),FMath::IsNearlyZero(Bike->CurrentSpeed));
    Key(EKeys::Gamepad_RightTriggerAxis, IE_Axis, 0.f); Process();
    Key(EKeys::Gamepad_LeftTriggerAxis, IE_Axis, 0.f); Process();
    Bike->CurrentSpeed=-200.f; Bike->Tick(.1f);
    TestTrue(TEXT("L2 release coasts reverse without sticky input"),FMath::IsNearlyEqual(Bike->CurrentSpeed,-160.f,1.f));
    Key(EKeys::SpaceBar, IE_Pressed, 1.f); Process();
    Bike->CurrentSpeed=0.f;
    for (int32 I=0; I<60; ++I) Bike->Tick(1.f/60.f);
    TestTrue(TEXT("Keyboard dedicated brake never selects reverse"),FMath::IsNearlyZero(Bike->CurrentSpeed));
    Key(EKeys::SpaceBar, IE_Released, 0.f); Process();
    Ground->Destroy();
    if (!TestNotNull(TEXT("Rear brake action installed"), PC->HandbrakeAction)
        || !TestNotNull(TEXT("Rider balance action installed"), PC->RiderBalanceAction)) return false;
    Key(EKeys::Gamepad_RightShoulder, IE_Pressed, 1.f); Process();
    Bike->CurrentSpeed = 1500.f; Bike->Tick(.1f);
    TestTrue(TEXT("R1 dispatches rear brake"), FMath::IsNearlyEqual(Bike->CurrentSpeed, 1401.f, 1.f));
    Key(EKeys::Gamepad_RightShoulder, IE_Released, 0.f); Process();
    Bike->CurrentSpeed = 1500.f; Bike->Tick(.1f);
    TestTrue(TEXT("Released R1 clears rear brake"), FMath::IsNearlyEqual(Bike->CurrentSpeed, 1460.f, 1.f));
    Bike->SetActorLocation(FVector(4000,0,1000));
    Bike->SetActorRotation(FRotator::ZeroRotator);
    Bike->VerticalVelocity = 0.f; Bike->bIsAirborne = true;
    Key(EKeys::Gamepad_LeftY, IE_Axis, -.8f); Process();
    Bike->Tick(.1f);
    const float PulledPitch = Bike->GetActorRotation().Pitch;
    TestTrue(TEXT("Pulling left stick back pitches nose up"), PulledPitch > 3.f);
    Key(EKeys::Gamepad_LeftY, IE_Axis, 0.f); Process();
    Key(EKeys::Gamepad_RightY, IE_Axis, .8f); Process();
    Bike->Tick(.1f);
    TestTrue(TEXT("Balance release recovers pitch while right stick only looks"), Bike->GetActorRotation().Pitch < PulledPitch);
    Key(EKeys::Gamepad_RightY, IE_Axis, 0.f); Process();
    Key(EKeys::LeftShift, IE_Pressed, 1.f); Process();
    TestTrue(TEXT("Keyboard wheelie input maps positive balance"), Input->GetActionValue(PC->RiderBalanceAction).Get<float>() > .9f);
    Key(EKeys::LeftShift, IE_Released, 0.f); Process();
    Key(EKeys::LeftControl, IE_Pressed, 1.f); Process();
    TestTrue(TEXT("Keyboard forward lean maps negative balance"), Input->GetActionValue(PC->RiderBalanceAction).Get<float>() < -.9f);
    Key(EKeys::LeftControl, IE_Released, 0.f); Process();
    Key(EKeys::LeftAlt, IE_Pressed, 1.f); Process();
    TestTrue(TEXT("Keyboard rear brake maps held action"), Input->GetActionValue(PC->HandbrakeAction).Get<bool>());
    Key(EKeys::LeftAlt, IE_Released, 0.f); Process();
    Bike->CurrentRider = nullptr;
    return true;
}
#endif
