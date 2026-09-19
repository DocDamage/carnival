#pragma once

#include "CoreMinimal.h"
#include "CarnivalTypes.generated.h"

UENUM(BlueprintType)
enum class ECarnivalRidePhase : uint8
{
    Closed,
    Loading,
    Locked,
    Running,
    Unloading
};

UENUM(BlueprintType)
enum class ECarnivalRideReaction : uint8
{
    Calm,
    Grip,
    LeanLeft,
    LeanRight,
    HandsUp,
    Laugh,
    Cheer,
    Scream,
    Brace,
    Relief
};

UENUM(BlueprintType)
enum class ECarnivalRestraintType : uint8
{
    None,
    LapBar,
    OverShoulder,
    HandleBars,
    SeatBelt,
    Custom
};

UENUM(BlueprintType)
enum class ECarnivalGuestArchetype : uint8
{
    Calm,
    ThrillSeeker,
    Nervous,
    ShowOff,
    Excitable,
    Stoic,
    MotionSensitive
};

UENUM(BlueprintType)
enum class ECarnivalGuestRole : uint8
{
    None,
    Guest,           // Park visitor — rides, queues, reacts.
    RideOperator,    // Operates a ride.
    FoodVendor,      // Food / drink stall.
    GameAttendant,   // Carnival game booth.
    TicketTaker,     // Entry / ticket booth.
    Entertainer,     // Mascot / street performer.
    Security,        // Patrol / security.
    Janitor          // Cleaning / maintenance.
};

USTRUCT(BlueprintType)
struct CARNIVALPOPULATION_API FCarnivalRideTelemetry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry")
    float Speed = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry")
    float LinearAcceleration = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry")
    float VerticalAcceleration = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry")
    float LateralAcceleration = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry")
    float AngularSpeed = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Telemetry", meta=(ClampMin="0.0", ClampMax="1.0"))
    float Intensity = 0.0f;
};

USTRUCT(BlueprintType)
struct CARNIVALPOPULATION_API FCarnivalGuestPersonality
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Personality")
    ECarnivalGuestArchetype Archetype = ECarnivalGuestArchetype::Calm;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Personality", meta=(ClampMin="0.0", ClampMax="1.0"))
    float Fear = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Personality", meta=(ClampMin="0.0", ClampMax="1.0"))
    float Excitement = 0.55f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Personality", meta=(ClampMin="0.0", ClampMax="1.0"))
    float Showmanship = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carnival|Personality", meta=(ClampMin="0.0", ClampMax="1.0"))
    float MotionSensitivity = 0.25f;
};
