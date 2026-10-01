#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "CarnivalCharacterMovementComponent.generated.h"

/**
 * Player movement. Walking into water that covers the whole character (a flooded tunnel or room) keeps the
 * feet on the floor instead of forcing swimming; ACarnivalPlayerCharacter switches between seabed walking
 * and swimming from there. Every other water entry is standard.
 */
UCLASS()
class CARNIVALGAME_API UCarnivalCharacterMovementComponent : public UCharacterMovementComponent
{
	GENERATED_BODY()

public:
	virtual void PhysicsVolumeChanged(class APhysicsVolume* NewVolume) override;
};
