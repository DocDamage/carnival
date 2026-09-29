#include "CarnivalPlayerController.h"
#include "CarnivalMotorcycle.h"
#include "CarnivalBoat.h"
#include "CarnivalHovercraft.h"
#include "CarnivalBumperCar.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputKeyEventArgs.h"
#include "EnhancedInputSubsystems.h"
#include "Misc/ConfigCacheIni.h"

namespace
{
constexpr const TCHAR* RemappingSection = TEXT("Carnival.ControlRemapping");
bool ReservedKey(FKey Key)
{
	return Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Right;
}
bool IsVehicle(const APawn* Pawn)
{
	return Pawn && (Pawn->IsA<ACarnivalMotorcycle>() || Pawn->IsA<ACarnivalBoat>() || Pawn->IsA<ACarnivalHovercraft>() || Pawn->IsA<ACarnivalBumperCar>());
}
bool CompatibleKey(FKey Original, FKey Candidate)
{
	return Candidate.IsValid() && !ReservedKey(Candidate)
		&& Original.IsGamepadKey() == Candidate.IsGamepadKey()
		&& Original.IsAxis1D() == Candidate.IsAxis1D()
		&& Original.IsAxis2D() == Candidate.IsAxis2D()
		&& Original.IsAxis3D() == Candidate.IsAxis3D();
}
}

void ACarnivalPlayerController::InitializeControlRemapping()
{
	if (bControlMappingsInitialized) return;
	bControlMappingsInitialized = true;
	auto CopyContext = [&](UInputMappingContext*& Context, const FString& Scope)
	{
		if (!Context) return;
		const FString SourcePath = Context->GetPathName();
		if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
			Subsystem->RemoveMappingContext(Context);
		Context = DuplicateObject<UInputMappingContext>(Context, this);
		for (int32 Index = 0; Index < Context->GetMappings().Num(); ++Index)
		{
			const auto& Mapping = Context->GetMapping(Index);
			if (!Mapping.Action || Mapping.Action == SettingsMenuAction || ReservedKey(Mapping.Key)) continue;
			FControlBinding Binding;
			Binding.Context = Context;
			Binding.MappingIndex = Index;
			Binding.DefaultKey = Mapping.Key;
			Binding.SaveId = SourcePath + TEXT("|") + Mapping.Action->GetPathName() + TEXT("|") + Mapping.Key.ToString();
			FString Name = Mapping.Action->GetName();
			Name.RemoveFromStart(TEXT("IA_"));
			Binding.Label = Scope + TEXT(" / ") + FName::NameToDisplayString(Name, false);
			ControlBindings.Add(Binding);
		}
	};
	CopyContext(DefaultMappingContext, TEXT("On foot"));
	CopyContext(MotorcycleMappingContext, TEXT("Vehicle"));
	// Load as a batch so swaps made across sessions do not depend on array order.
	for (const auto& Binding : ControlBindings)
	{
		FString SavedKey;
		if (GConfig && GConfig->GetString(RemappingSection, *Binding.SaveId, SavedKey, GGameUserSettingsIni))
		{
			const FKey Key{FName(*SavedKey)};
			if (CompatibleKey(Binding.DefaultKey, Key)) Binding.Context->GetMapping(Binding.MappingIndex).Key = Key;
		}
	}
	// Preserve authored multi-action keys, but reject newly introduced conflicts in a damaged config.
	bool bInvalid = false;
	for (int32 A = 0; A < ControlBindings.Num(); ++A)
		for (int32 B = A + 1; B < ControlBindings.Num(); ++B)
		{
			const auto& Left = ControlBindings[A];
			const auto& Right = ControlBindings[B];
			if (Left.Context == Right.Context && Left.DefaultKey != Right.DefaultKey
				&& Left.Context->GetMapping(Left.MappingIndex).Key == Right.Context->GetMapping(Right.MappingIndex).Key)
				bInvalid = true;
		}
	for (const auto& Binding : ControlBindings)
	{
		const auto& Mapping = Binding.Context->GetMapping(Binding.MappingIndex);
		if (Mapping.Key == Binding.DefaultKey) continue;
		for (int32 Index = 0; Index < Binding.Context->GetMappings().Num(); ++Index)
			if (Index != Binding.MappingIndex && Binding.Context->GetMapping(Index).Key == Mapping.Key)
				bInvalid = true;
	}
	if (bInvalid)
		for (const auto& Binding : ControlBindings) Binding.Context->GetMapping(Binding.MappingIndex).Key = Binding.DefaultKey;
	RebuildControlMappings();
}

void ACarnivalPlayerController::RebuildControlMappings()
{
	FlushPressedKeys();
	if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (DefaultMappingContext) Subsystem->RemoveMappingContext(DefaultMappingContext);
		if (MotorcycleMappingContext) Subsystem->RemoveMappingContext(MotorcycleMappingContext);
		auto* Active = IsVehicle(GetPawn()) ? MotorcycleMappingContext : DefaultMappingContext;
		if (Active) Subsystem->AddMappingContext(Active, 0);
		Subsystem->RequestRebuildControlMappings();
	}
}

bool ACarnivalPlayerController::RemapControl(int32 BindingIndex, FKey NewKey)
{
	if (!ControlBindings.IsValidIndex(BindingIndex)) return false;
	const auto& Binding = ControlBindings[BindingIndex];
	if (!CompatibleKey(Binding.DefaultKey, NewKey))
	{
		ControlRemappingFeedback = TEXT("Choose the same device and input type. Escape and Options stay available for menus.");
		return false;
	}
	for (int32 Index = 0; Index < Binding.Context->GetMappings().Num(); ++Index)
	{
		if (Index != Binding.MappingIndex && Binding.Context->GetMapping(Index).Key == NewKey
			&& Binding.Context->GetMapping(Binding.MappingIndex).Key != NewKey)
		{
			ControlRemappingFeedback = TEXT("Already assigned in this context. Reassign that control first.");
			return false;
		}
	}
	ClearCurrentPawnInputs(false);
	Binding.Context->GetMapping(Binding.MappingIndex).Key = NewKey;
	RebuildControlMappings();
	SaveControlRemapping();
	ControlRemappingFeedback = TEXT("Saved.");
	return true;
}

void ACarnivalPlayerController::SaveControlRemapping() const
{
	if (!GConfig) return;
	for (const auto& Binding : ControlBindings)
		GConfig->SetString(RemappingSection, *Binding.SaveId, *Binding.Context->GetMapping(Binding.MappingIndex).Key.ToString(), GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

void ACarnivalPlayerController::RestoreControlDefaults()
{
	ClearCurrentPawnInputs(false);
	for (const auto& Binding : ControlBindings) Binding.Context->GetMapping(Binding.MappingIndex).Key = Binding.DefaultKey;
	RebuildControlMappings();
	SaveControlRemapping();
	ControlRemappingFeedback = TEXT("Default bindings restored and saved.");
}

FString ACarnivalPlayerController::GetKeyLabel(FKey Key) const
{
	if (Key == EKeys::Gamepad_Left2D) return TEXT("Left stick");
	if (Key == EKeys::Gamepad_Right2D) return TEXT("Right stick");
	if (Key == EKeys::Gamepad_LeftX) return TEXT("Left stick X");
	if (Key == EKeys::Gamepad_LeftY) return TEXT("Left stick Y");
	if (Key == EKeys::Gamepad_RightX) return TEXT("Right stick X");
	if (Key == EKeys::Gamepad_RightY) return TEXT("Right stick Y");
	if (Key == EKeys::Gamepad_DPad_Right) return TEXT("D-pad Right");
	if (Key == EKeys::Gamepad_DPad_Left) return TEXT("D-pad Left");
	if (Key == EKeys::Gamepad_DPad_Up) return TEXT("D-pad Up");
	if (Key == EKeys::Gamepad_DPad_Down) return TEXT("D-pad Down");
	if (bPlayStationPrompts)
	{
		if (Key == EKeys::Gamepad_FaceButton_Bottom) return TEXT("Cross");
		if (Key == EKeys::Gamepad_FaceButton_Right) return TEXT("Circle");
		if (Key == EKeys::Gamepad_FaceButton_Left) return TEXT("Square");
		if (Key == EKeys::Gamepad_FaceButton_Top) return TEXT("Triangle");
		if (Key == EKeys::Gamepad_LeftShoulder) return TEXT("L1");
		if (Key == EKeys::Gamepad_RightShoulder) return TEXT("R1");
		if (Key == EKeys::Gamepad_LeftTriggerAxis) return TEXT("L2");
		if (Key == EKeys::Gamepad_RightTriggerAxis) return TEXT("R2");
	}
	return Key.GetDisplayName().ToString();
}

FString ACarnivalPlayerController::GetActionKeyLabel(const UInputAction* Action) const
{
	const auto* Context = IsVehicle(GetPawn()) ? MotorcycleMappingContext : DefaultMappingContext;
	TArray<FString> Labels;
	if (Action && Context)
		for (const auto& Mapping : Context->GetMappings())
			if (Mapping.Action == Action && Mapping.Key.IsGamepadKey() == bUsingGamepad) Labels.AddUnique(GetKeyLabel(Mapping.Key));
	return Labels.IsEmpty() ? TEXT("Unbound") : FString::Join(Labels, TEXT(" / "));
}

TArray<int32> ACarnivalPlayerController::GetVisibleControlBindings() const
{
	TArray<int32> Rows;
	for (int32 Index = 0; Index < ControlBindings.Num(); ++Index)
		if (ControlBindings[Index].DefaultKey.IsGamepadKey() == bRemapGamepad) Rows.Add(Index);
	return Rows;
}

TArray<FString> ACarnivalPlayerController::GetControlRemappingLines() const
{
	TArray<FString> Lines;
	const auto Rows = GetVisibleControlBindings();
	Lines.Add(bRemapGamepad ? TEXT("Controller bindings (Left/Right switches device)") : TEXT("Keyboard / mouse bindings (Left/Right switches device)"));
	const int32 First = (ControlRemappingSelection / 10) * 10;
	for (int32 Row = First; Row < FMath::Min(First + 10, Rows.Num() + 1); ++Row)
	{
		FString Label = TEXT("Restore all binding defaults");
		if (Rows.IsValidIndex(Row))
		{
			const auto& Binding = ControlBindings[Rows[Row]];
			Label = Binding.Label + TEXT(" [") + GetKeyLabel(Binding.DefaultKey) + TEXT("]: ")
				+ GetKeyLabel(Binding.Context->GetMapping(Binding.MappingIndex).Key);
		}
		Lines.Add((Row == ControlRemappingSelection ? TEXT("> ") : TEXT("  ")) + Label);
	}
	Lines.Add(FString::Printf(TEXT("%d / %d"), ControlRemappingSelection + 1, Rows.Num() + 1));
	Lines.Add(bCapturingControl ? TEXT("Press a new button or move the matching axis. Escape / Options cancels.")
		: TEXT("Up/Down: select. Enter / Cross / A: rebind. Escape / Circle / B: back."));
	Lines.Add(ControlRemappingFeedback);
	return Lines;
}

void ACarnivalPlayerController::HandleControlRemappingInput(const FInputKeyEventArgs& Params)
{
	const FKey Key = Params.Key;
	const auto Rows = GetVisibleControlBindings();
	if (bCapturingControl)
	{
		if (Params.Event == IE_Pressed && ReservedKey(Key))
		{
			bCapturingControl = false;
			ControlRemappingFeedback = TEXT("Cancelled.");
		}
		else if (Rows.IsValidIndex(ControlRemappingSelection)
			&& (Params.Event == IE_Pressed || (Params.Event == IE_Axis && FMath::Abs(Params.AmountDepressed) > .65f)))
		{
			FKey Captured = Key;
			const FKey Original = ControlBindings[Rows[ControlRemappingSelection]].DefaultKey;
			// Windows emits stick axes separately even when an IMC maps a composite 2D stick.
			if (Original.IsAxis2D())
			{
				if (Key == EKeys::Gamepad_LeftX || Key == EKeys::Gamepad_LeftY) Captured = EKeys::Gamepad_Left2D;
				else if (Key == EKeys::Gamepad_RightX || Key == EKeys::Gamepad_RightY) Captured = EKeys::Gamepad_Right2D;
				else if (Key == EKeys::MouseX || Key == EKeys::MouseY) Captured = EKeys::Mouse2D;
			}
			if (RemapControl(Rows[ControlRemappingSelection], Captured)) bCapturingControl = false;
		}
		return;
	}
	if (Params.Event != IE_Pressed && Params.Event != IE_Repeat) return;
	if (ReservedKey(Key) || Key == EKeys::Gamepad_FaceButton_Right) bControlRemappingOpen = false;
	else if (Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up)
		ControlRemappingSelection = (ControlRemappingSelection + Rows.Num()) % (Rows.Num() + 1);
	else if (Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down)
		ControlRemappingSelection = (ControlRemappingSelection + 1) % (Rows.Num() + 1);
	else if (Key == EKeys::Left || Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_DPad_Right)
	{
		bRemapGamepad = !bRemapGamepad;
		ControlRemappingSelection = 0;
	}
	else if (Params.Event == IE_Pressed && (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom))
	{
		if (Rows.IsValidIndex(ControlRemappingSelection)) bCapturingControl = true;
		else RestoreControlDefaults();
		ControlRemappingFeedback.Reset();
	}
}
