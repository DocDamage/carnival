// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "CarnivalMovementTypes.generated.h"

/** Character locomotion states covering extensive movement modes */
UENUM(BlueprintType)
enum class ECarnivalLocomotionState : uint8
{
	Walking				UMETA(DisplayName = "Walking"),
	Jogging				UMETA(DisplayName = "Jogging"),
	Sprinting			UMETA(DisplayName = "Sprinting"),
	Crouching			UMETA(DisplayName = "Crouching"),
	Prone				UMETA(DisplayName = "Prone"),
	Jumping				UMETA(DisplayName = "Jumping"),
	Falling				UMETA(DisplayName = "Falling"),
	LandingRoll			UMETA(DisplayName = "Landing Roll"),
	Vaulting			UMETA(DisplayName = "Vaulting"),
	Mantling			UMETA(DisplayName = "Mantling"),
	LadderClimbing		UMETA(DisplayName = "Ladder Climbing"),
	LedgeClimbing		UMETA(DisplayName = "Ledge Climbing"),
	Swimming			UMETA(DisplayName = "Swimming"),
	RidingMotorcycle	UMETA(DisplayName = "Riding Motorcycle")
	RidingMotorcycle	UMETA(DisplayName = "Riding Motorcycle"),
	DrivingBoat			UMETA(DisplayName = "Driving Boat"),
	PilotingHovercraft	UMETA(DisplayName = "Piloting Hovercraft")
};

/** Weapon types currently equipped */
UENUM(BlueprintType)
enum class ECarnivalWeaponType : uint8
{
	Unarmed			UMETA(DisplayName = "Unarmed"),
	Sword			UMETA(DisplayName = "Sword"),
	SwordAndShield	UMETA(DisplayName = "Sword & Shield"),
	Knife			UMETA(DisplayName = "Knife"),
	Revolver		UMETA(DisplayName = "Revolver")
};

/** Motorcycle physics simulation mode (switchable in game settings) */
UENUM(BlueprintType)
enum class EMotorcyclePhysicsMode : uint8
{
	Arcade			UMETA(DisplayName = "Arcade (Responsive / No-Tip)"),
	ChaosPhysics	UMETA(DisplayName = "Chaos Physics (Full 2-Wheel Simulation)")
};

