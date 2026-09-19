#include "CarnivalGuestLibrary.h"
#include "CarnivalActivityZone.h"

FText UCarnivalGuestLibrary::GetRoleDisplayName(ECarnivalGuestRole Role)
{
    switch (Role)
    {
    case ECarnivalGuestRole::Guest:          return NSLOCTEXT("Carnival", "RoleGuest", "Guest");
    case ECarnivalGuestRole::RideOperator:   return NSLOCTEXT("Carnival", "RoleRideOperator", "Ride Operator");
    case ECarnivalGuestRole::FoodVendor:     return NSLOCTEXT("Carnival", "RoleFoodVendor", "Food Vendor");
    case ECarnivalGuestRole::GameAttendant:  return NSLOCTEXT("Carnival", "RoleGameAttendant", "Game Attendant");
    case ECarnivalGuestRole::TicketTaker:    return NSLOCTEXT("Carnival", "RoleTicketTaker", "Ticket Taker");
    case ECarnivalGuestRole::Entertainer:    return NSLOCTEXT("Carnival", "RoleEntertainer", "Entertainer");
    case ECarnivalGuestRole::Security:       return NSLOCTEXT("Carnival", "RoleSecurity", "Security");
    case ECarnivalGuestRole::Janitor:        return NSLOCTEXT("Carnival", "RoleJanitor", "Janitor");
    default:                                 return NSLOCTEXT("Carnival", "RoleNone", "Unknown");
    }
}

bool UCarnivalGuestLibrary::IsStaff(ECarnivalGuestRole Role)
{
    return Role != ECarnivalGuestRole::None && Role != ECarnivalGuestRole::Guest;
}

ECarnivalActivityType UCarnivalGuestLibrary::GetRoleActivityType(ECarnivalGuestRole Role)
{
    switch (Role)
    {
    case ECarnivalGuestRole::Guest:          return ECarnivalActivityType::Wander;
    case ECarnivalGuestRole::RideOperator:   return ECarnivalActivityType::RideQueue;
    case ECarnivalGuestRole::FoodVendor:     return ECarnivalActivityType::Food;
    case ECarnivalGuestRole::GameAttendant:  return ECarnivalActivityType::GameBooth;
    case ECarnivalGuestRole::TicketTaker:    return ECarnivalActivityType::Exit;
    case ECarnivalGuestRole::Entertainer:    return ECarnivalActivityType::Spectator;
    case ECarnivalGuestRole::Security:       return ECarnivalActivityType::Wander;
    case ECarnivalGuestRole::Janitor:        return ECarnivalActivityType::Wander;
    default:                                 return ECarnivalActivityType::Wander;
    }
}

TArray<ECarnivalGuestRole> UCarnivalGuestLibrary::GetAllRoles()
{
    return {
        ECarnivalGuestRole::Guest,
        ECarnivalGuestRole::RideOperator,
        ECarnivalGuestRole::FoodVendor,
        ECarnivalGuestRole::GameAttendant,
        ECarnivalGuestRole::TicketTaker,
        ECarnivalGuestRole::Entertainer,
        ECarnivalGuestRole::Security,
        ECarnivalGuestRole::Janitor
    };
}
