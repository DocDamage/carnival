#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalPassengerInterface.h"
#include "CarnivalGuestCharacter.generated.h"

class UCarnivalRidePassengerComponent;

/**
 * Asset-agnostic carnival guest character. Derive a Blueprint, assign a mesh
 * (MetaHuman or a placeholder mannequin), and the guest can board rides and
 * react to ride motion. Implements ICarnivalPassengerInterface so the visual
 * hooks (boarded / reaction / unboarded) are Blueprint-overridable.
 */
UCLASS(Blueprintable, Abstract)
class CARNIVALPOPULATION_API ACarnivalGuestCharacter : public ACharacter, public ICarnivalPassengerInterface
{
    GENERATED_BODY()

public:
    ACarnivalGuestCharacter();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Carnival")
    TObjectPtr<UCarnivalRidePassengerComponent> PassengerComponent;

    // ICarnivalPassengerInterface (BlueprintNativeEvent visual hooks).
    virtual void CarnivalRideBoarded_Implementation(AActor* RideActor, FName SeatId, ECarnivalRestraintType RestraintType) override;
    virtual void CarnivalRideReactionChanged_Implementation(ECarnivalRideReaction Reaction, float Strength, const FCarnivalRideTelemetry& Telemetry) override;
    virtual void CarnivalRideUnboarded_Implementation(AActor* RideActor) override;
};
