// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "CarnivalMovementTypes.h"
#include "CarnivalHUD.generated.h"

class ACarnivalPlayerCharacter;
class ACarnivalPlayerController;
class ACarnivalMotorcycle;
class UCarnivalMissionSubsystem;

UCLASS()
class CARNIVALGAME_API ACarnivalHUD : public AHUD
{
	GENERATED_BODY()

public:
	ACarnivalHUD();

	virtual void DrawHUD() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bShowHelpOverlay = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bShowSettingsMenu = false;

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ToggleSettingsMenu();

protected:
	void DrawSessionMenu(ACarnivalPlayerController* PC);
	void DrawVehicleControls(ACarnivalPlayerController* PC);
	void DrawTelemetry(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawBuildModeHUD(ACarnivalPlayerCharacter* Char);
	void DrawSwimControls(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawSettingsMenu(ACarnivalPlayerController* PC);
	void DrawActivityOverlay(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawStoryMissionOverlay(ACarnivalPlayerController* PC);
	void DrawStoryInteractionPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawPlayerRecoveryPrompt(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawRideInteraction(ACarnivalPlayerCharacter* Char, ACarnivalPlayerController* PC);
	void DrawCrosshair();

	void DrawBoxWithText(float X, float Y, float Width, float Height, const FString& Header, const TArray<FString>& Lines, const FLinearColor& BoxColor, const FLinearColor& HeaderColor, const FLinearColor& TextColor);
};
