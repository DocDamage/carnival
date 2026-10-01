#include "CarnivalCharacterMovementComponent.h"
#include "CarnivalWaterVolume.h"
#include "GameFramework/Character.h"

void UCarnivalCharacterMovementComponent::PhysicsVolumeChanged(APhysicsVolume* NewVolume)
{
	const ACarnivalWaterVolume* Water = Cast<ACarnivalWaterVolume>(NewVolume);
	if (Water && Water->bWaterVolume && IsMovingOnGround() && CharacterOwner && UpdatedComponent)
	{
		const float Top = UpdatedComponent->GetComponentLocation().Z + CharacterOwner->GetSimpleCollisionHalfHeight();
		if (Top < Water->GetSurfaceZ() - 5.f)
		{
			return;
		}
	}
	Super::PhysicsVolumeChanged(NewVolume);
}
