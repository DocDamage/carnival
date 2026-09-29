#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "CarnivalPlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputKeyEventArgs.h"
#include "EnhancedInputSubsystemInterface.h"
#include "EnhancedPlayerInput.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

class FCarnivalRemappingInputSubsystem : public IEnhancedInputSubsystemInterface
{
public:
	UEnhancedPlayerInput* Input = nullptr;
	TMap<TObjectPtr<const UInputAction>, FInjectedInput> Injected;
	virtual UEnhancedPlayerInput* GetPlayerInput() const override { return Input; }
	virtual TMap<TObjectPtr<const UInputAction>, FInjectedInput>& GetContinuouslyInjectedInputs() override { return Injected; }
};

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalSavedRemappingTest, "Carnival.Input.SavedRemapping",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCarnivalSavedRemappingTest::RunTest(const FString&)
{
	const FString OriginalIni = GGameUserSettingsIni;
	GGameUserSettingsIni = FPaths::ProjectSavedDir() / TEXT("Automation/ControlRemappingTest.ini");
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(GGameUserSettingsIni), true);
	// UE 5.8 will not cache a nonexistent ad-hoc config via LoadFile. Register
	// an empty isolated file; production GameUserSettings is already registered.
	GConfig->Add(GGameUserSettingsIni, FConfigFile());
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("SavedRemapping"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT
	{
		World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World);
		GConfig->UnloadFile(GGameUserSettingsIni);
		IFileManager::Get().Delete(*GGameUserSettingsIni);
		GGameUserSettingsIni = OriginalIni;
	};
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL); World->InitializeActorsForPlay(URL); World->BeginPlay();
	auto* Context = NewObject<UInputMappingContext>();
	auto* VehicleContext = NewObject<UInputMappingContext>();
	auto* Interact = NewObject<UInputAction>();
	auto* Jump = NewObject<UInputAction>();
	auto* Axis = NewObject<UInputAction>();
	Axis->ValueType = EInputActionValueType::Axis1D;
	Context->MapKey(Interact, EKeys::E);
	Context->MapKey(Jump, EKeys::SpaceBar);
	Context->MapKey(Interact, EKeys::Gamepad_FaceButton_Top);
	Context->MapKey(Axis, EKeys::S).Modifiers.Add(NewObject<UInputModifierNegate>(Context));
	VehicleContext->MapKey(Interact, EKeys::F);
	auto SpawnController = [&]()
	{
		auto* PC = World->SpawnActorDeferred<ACarnivalPlayerController>(ACarnivalPlayerController::StaticClass(), FTransform::Identity);
		PC->DefaultMappingContext = Context;
		PC->MotorcycleMappingContext = VehicleContext;
		PC->ContextInteractAction = Interact;
		PC->FinishSpawning(FTransform::Identity);
		PC->InitInputSystem();
		return PC;
	};
	auto* PC = SpawnController();
	TestEqual(TEXT("Both movement contexts expose bindings"), PC->ControlBindings.Num(), 5);
	TestTrue(TEXT("Runtime contexts are copies"), PC->DefaultMappingContext != Context && PC->MotorcycleMappingContext != VehicleContext);
	TestFalse(TEXT("Conflicts cannot replace jump with interaction"), PC->RemapControl(0, EKeys::SpaceBar));
	TestFalse(TEXT("Menu escape cannot be rebound"), PC->RemapControl(0, EKeys::Escape));
	TestFalse(TEXT("A digital button cannot become an analog axis"), PC->RemapControl(0, EKeys::MouseX));
	TestFalse(TEXT("A keyboard slot cannot become a gamepad button"), PC->RemapControl(0, EKeys::Gamepad_FaceButton_Left));
	TestTrue(TEXT("A free keyboard binding saves"), PC->RemapControl(0, EKeys::G));
	TestEqual(TEXT("Prompt follows remapping"), PC->GetActionKeyLabel(Interact), EKeys::G.GetDisplayName().ToString());
	TestTrue(TEXT("Directional key can be remapped"), PC->RemapControl(3, EKeys::Down));
	TestEqual(TEXT("Direction modifier survives"), PC->DefaultMappingContext->GetMapping(3).Modifiers.Num(), 1);
	TestEqual(TEXT("Source asset is untouched"), Context->GetMapping(0).Key, EKeys::E);
	FCarnivalRemappingInputSubsystem InputSubsystem;
	InputSubsystem.Input = Cast<UEnhancedPlayerInput>(PC->PlayerInput);
	if (!TestNotNull(TEXT("Enhanced Input runtime exists"), InputSubsystem.Input)) return false;
	FModifyContextOptions Options;
	Options.bForceImmediately = true;
	InputSubsystem.AddMappingContext(PC->DefaultMappingContext, 0, Options);
	auto DispatchKey = [&](FKey Key, EInputEvent Event)
	{
		PC->InputKey(FInputKeyEventArgs::CreateSimulated(Key, Event, Event == IE_Pressed ? 1.f : 0.f));
		InputSubsystem.Input->ProcessInputStack({PC->InputComponent}, 1.f / 60.f, false);
	};
	DispatchKey(EKeys::E, IE_Pressed);
	TestFalse(TEXT("Old key no longer activates interaction"), InputSubsystem.Input->GetActionValue(Interact).Get<bool>());
	DispatchKey(EKeys::E, IE_Released);
	DispatchKey(EKeys::G, IE_Pressed);
	TestTrue(TEXT("Remapped key activates through real Enhanced Input dispatch"), InputSubsystem.Input->GetActionValue(Interact).Get<bool>());
	DispatchKey(EKeys::G, IE_Released);
	TestFalse(TEXT("Releasing remapped key clears the action"), InputSubsystem.Input->GetActionValue(Interact).Get<bool>());
	GConfig->Flush(false, GGameUserSettingsIni);
	FString SavedContents;
	TestTrue(TEXT("Bindings are written to disk"), FFileHelper::LoadFileToString(SavedContents, *GGameUserSettingsIni));
	TestTrue(TEXT("Saved file contains binding section"), SavedContents.Contains(TEXT("Carnival.ControlRemapping")));
	GConfig->UnloadFile(GGameUserSettingsIni);
	GConfig->LoadFile(GGameUserSettingsIni);
	auto* Reloaded = SpawnController();
	TestEqual(TEXT("Fresh controller reloads binding from disk"), Reloaded->DefaultMappingContext->GetMapping(0).Key, EKeys::G);
	TestEqual(TEXT("Fresh controller reloads directional binding"), Reloaded->DefaultMappingContext->GetMapping(3).Key, EKeys::Down);
	Reloaded->bUsingGamepad = true;
	TestTrue(TEXT("Controller button can be rebound"), Reloaded->RemapControl(2, EKeys::Gamepad_FaceButton_Left));
	TestEqual(TEXT("PlayStation prompt uses new face button"), Reloaded->GetActionKeyLabel(Interact), FString(TEXT("Square")));
	Reloaded->RestoreControlDefaults();
	TestEqual(TEXT("Restore resets keyboard"), Reloaded->DefaultMappingContext->GetMapping(0).Key, EKeys::E);
	TestEqual(TEXT("Restore resets controller"), Reloaded->DefaultMappingContext->GetMapping(2).Key, EKeys::Gamepad_FaceButton_Top);
	PC->ToggleSettingsMenu();
	PC->SettingsMenuSelection = 5;
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Enter, IE_Pressed, 1.f));
	TestTrue(TEXT("Settings opens remapping"), PC->bControlRemappingOpen);
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Enter, IE_Pressed, 1.f));
	TestTrue(TEXT("Confirm enters capture"), PC->bCapturingControl);
	PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::Escape, IE_Pressed, 1.f));
	TestTrue(TEXT("Cancel capture keeps settings paused"), !PC->bCapturingControl && PC->bSettingsMenuOpen && World->IsPaused());
	PC->ToggleSettingsMenu();
	return true;
}
#endif
