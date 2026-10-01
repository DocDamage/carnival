#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalPlayerController.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalMotorcycle.h"
#include "InputKeyEventArgs.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FControllerDisconnectRecoveryTest, "Carnival.Input.ControllerDisconnectRecovery",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FControllerDisconnectRecoveryTest::RunTest(const FString&)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("ControllerDisconnectRecovery"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL);
	World->InitializeActorsForPlay(URL);
	World->BeginPlay();

	FActorSpawnParameters Spawn;
	Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	auto* PC = World->SpawnActor<ACarnivalPlayerController>(FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
	PC->InitInputSystem();
	auto* Bike = World->SpawnActor<ACarnivalMotorcycle>(FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
	auto* Rider = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(300.f, 0.f, 100.f), FRotator::ZeroRotator, Spawn);
	PC->Possess(Bike);
	Bike->CurrentRider = Rider;

	const FInputDeviceId DeviceId = FInputDeviceId::CreateFromInternalId(27);
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_RightTriggerAxis, IE_Axis, .8f, -1, DeviceId));
	TestTrue(TEXT("A gamepad event records the active controller"), PC->bUsingGamepad);
	Bike->InputThrottle(1.f);
	Bike->InputSteering(.8f);
	Bike->InputBrake(.5f);
	Bike->InputBrakeReverse(.7f);
	Bike->InputHandbrake(true);
	Bike->InputRiderBalance(-.6f);

	Instance->OnInputDeviceConnectionChange.Broadcast(EInputDeviceConnectionState::Disconnected, PC->GetPlatformUserId(), DeviceId);
	TestTrue(TEXT("Losing the active controller pauses gameplay"), PC->bControllerDisconnectPaused && World->IsPaused());
	Bike->CurrentSpeed = 0.f;
	Bike->Tick(1.f / 60.f);
	TestTrue(TEXT("Losing the controller clears throttle before bike simulation"), FMath::IsNearlyZero(Bike->CurrentSpeed));

	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Enter, IE_Pressed, 1.f));
	TestFalse(TEXT("Keyboard input resumes after controller loss"), PC->bControllerDisconnectPaused || World->IsPaused());

	Instance->OnInputDeviceConnectionChange.Broadcast(EInputDeviceConnectionState::Connected, PC->GetPlatformUserId(), DeviceId);
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_FaceButton_Bottom, IE_Pressed, 1.f, -1, DeviceId));
	TestTrue(TEXT("A reconnected controller becomes the active input device"), PC->bUsingGamepad);
	Instance->OnInputDeviceConnectionChange.Broadcast(EInputDeviceConnectionState::Disconnected, PC->GetPlatformUserId(), DeviceId);
	TestTrue(TEXT("A second controller loss pauses gameplay again"), PC->bControllerDisconnectPaused && World->IsPaused());
	Instance->OnInputDeviceConnectionChange.Broadcast(EInputDeviceConnectionState::Connected, PC->GetPlatformUserId(), DeviceId);
	TestTrue(TEXT("Reconnect alone waits for deliberate input"), PC->bControllerDisconnectPaused && World->IsPaused());
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_FaceButton_Bottom, IE_Pressed, 1.f, -1, DeviceId));
	TestFalse(TEXT("Controller input resumes after reconnect"), PC->bControllerDisconnectPaused || World->IsPaused());
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_Special_Right, IE_Pressed, 1.f, -1, DeviceId));
	TestTrue(TEXT("Options opens a controller-operable pause menu"), PC->bSessionMenuOpen && World->IsPaused());
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_DPad_Down, IE_Pressed, 1.f, -1, DeviceId));
	TestEqual(TEXT("D-pad navigates the paused session menu"), PC->SessionMenuSelection, 1);
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Gamepad_Special_Right, IE_Pressed, 1.f, -1, DeviceId));
	TestFalse(TEXT("Options closes the session menu and resumes play"), PC->bSessionMenuOpen || World->IsPaused());
	return true;
}
#endif
