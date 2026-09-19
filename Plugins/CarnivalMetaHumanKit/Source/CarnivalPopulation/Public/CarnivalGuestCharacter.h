#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CarnivalPassengerInterface.h"
#include "CarnivalGuestCharacter.generated.h"

class UCarnivalRidePassengerComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCarnivalRoleChangedSignature, ECarnivalGuestRole, NewRole);

/**
 * Asset-agnostic carnival guest character. Derive a Blueprint, assign a mesh
 * (MetaHuman or a placeholder mannequin), and the guest can board rides and
 * react to ride motion. Implements ICarnivalPassengerInterface so the visual
 * hooks (boarded / reaction / unboarded) are Blueprint-overridable.
 *
 * Carries an ECarnivalGuestRole (job) with a Blueprint-overridable
 * ApplyRoleLook hook so each role can swap to a different mesh/outfit.
 */
UCLASS(Blueprintable, Abstract)
class CARNIVALPOPULATION_API ACarnivalGuestCharacter : public ACharacter, public ICarnivalPassengerInterface
{
    GENERATED_BODY()

public:
    ACarnivalGuestCharacter();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Carnival")
    TObjectPtr<UCarnivalRidePassengerComponent> PassengerComponent;

    // --- Role / job ---
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Role")
    ECarnivalGuestRole GuestRole = ECarnivalGuestRole::Guest;

    UPROPERTY(BlueprintAssignable, Category="Carnival|Role")
    FCarnivalRoleChangedSignature OnRoleChanged;

    UFUNCTION(BlueprintCallable, Category="Carnival|Role")
    void SetGuestRole(ECarnivalGuestRole NewRole);

    UFUNCTION(BlueprintPure, Category="Carnival|Role")
    ECarnivalGuestRole GetGuestRole() const { return GuestRole; }

    // Blueprint-overridable: assign the mesh/material/outfit for the role.
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Carnival|Role")
    void ApplyRoleLook(ECarnivalGuestRole NewRole);

    // ICarnivalPassengerInterface (BlueprintNativeEvent visual hooks).
    virtual void CarnivalRideBoarded_Implementation(AActor* RideActor, FName SeatId, ECarnivalRestraintType RestraintType) override;
    virtual void CarnivalRideReactionChanged_Implementation(ECarnivalRideReaction Reaction, float Strength, const FCarnivalRideTelemetry& Telemetry) override;
    virtual void CarnivalRideUnboarded_Implementation(AActor* RideActor) override;

protected:
    virtual void BeginPlay() override;
};
