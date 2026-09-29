#include "CarnivalGuestCharacter.h"
#include "CarnivalRidePassengerComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"

ACarnivalGuestCharacter::ACarnivalGuestCharacter()
{
    PassengerComponent = CreateDefaultSubobject<UCarnivalRidePassengerComponent>(TEXT("PassengerComponent"));
}

void ACarnivalGuestCharacter::BeginPlay()
{
    Super::BeginPlay();
    // Roaming guests must never seal a doorway or pin the player against a ride.
    // Keep world collision for walking, while crowd steering handles separation.
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    GetCapsuleComponent()->SetCanEverAffectNavigation(false);
    GetMesh()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    GetMesh()->SetCanEverAffectNavigation(false);
    ApplyRoleLook(GuestRole);
}

void ACarnivalGuestCharacter::SetGuestRole(ECarnivalGuestRole NewRole)
{
    if (GuestRole == NewRole)
    {
        return;
    }
    GuestRole = NewRole;
    OnRoleChanged.Broadcast(NewRole);
    ApplyRoleLook(NewRole);
}

void ACarnivalGuestCharacter::ApplyRoleLook_Implementation(ECarnivalGuestRole NewRole)
{
    // Blueprint-overridable: assign the mesh / outfit for the role.
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
