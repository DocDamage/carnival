// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalGameMode.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalPlayerController.h"
#include "CarnivalHUD.h"

ACarnivalGameMode::ACarnivalGameMode()
{
	DefaultPawnClass = ACarnivalPlayerCharacter::StaticClass();
	PlayerControllerClass = ACarnivalPlayerController::StaticClass();
	HUDClass = ACarnivalHUD::StaticClass();
}

