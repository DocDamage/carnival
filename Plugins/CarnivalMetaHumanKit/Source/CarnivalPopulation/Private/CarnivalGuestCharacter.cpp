#include "CarnivalGuestCharacter.h"
#include "CarnivalRidePassengerComponent.h"

ACarnivalGuestCharacter::ACarnivalGuestCharacter()
{
    PassengerComponent = CreateDefaultSubobject<UCarnivalRidePassengerComponent>(TEXT("PassengerComponent"));
}

void ACarnivalGuestCharacter::CarnivalRideBoarded_Implementation(AActor* RideActor, FName SeatId, ECarnivalRestraintType RestraintType)
{
    // Blueprint-overridable visual hook (play a "sit down" montage, snap IK, etc.).
}

void ACarnivalGuestCharacter::CarnivalRideReactionChanged_Implementation(ECarnivalRideReaction Reaction, float Strength, const FCarnivalRideTelemetry& Telemetry)
{
    // Blueprint-overridable visual hook (drive facial/body animation from Reaction/Strength).
}

void ACarnivalGuestCharacter::CarnivalRideUnboarded_Implementation(AActor* RideActor)
{
    // Blueprint-overridable visual hook (play a "stand up" montage, restore locomotion).
}
