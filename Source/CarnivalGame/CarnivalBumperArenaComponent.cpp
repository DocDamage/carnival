#include "CarnivalBumperArenaComponent.h"
#include "CarnivalBumperCar.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalRideOperationComponent.h"

bool UCarnivalBumperArenaComponent::InitializeArena()
{
    if (HalfExtent.X < 200.f || HalfExtent.Y < 200.f || Cars.IsEmpty()) return false;
    for (const auto& Car : Cars)
    {
        if (!IsValid(Car) || (Car->Arena && Car->Arena != this)) return false;
        Car->Arena = this;
    }
    return true;
}

UCarnivalRideOperationComponent* UCarnivalBumperArenaComponent::GetOperation() const
{
    return GetOwner() ? GetOwner()->FindComponentByClass<UCarnivalRideOperationComponent>() : nullptr;
}

bool UCarnivalBumperArenaComponent::IsDrivingEnabled() const
{
    const auto* Operation = GetOperation();
    return Operation && Operation->IsReady() && Operation->State == ECarnivalOperationState::Running;
}

bool UCarnivalBumperArenaComponent::ContainsCarLocation(FVector WorldLocation, float Radius) const
{
    if (!GetOwner()) return false;
    const FTransform Transform = GetOwner()->GetActorTransform();
    const FVector Local = Transform.InverseTransformPosition(WorldLocation) - LocalCenter;
    const FVector Scale = Transform.GetScale3D().GetAbs();
    return FMath::Abs(Local.X) <= HalfExtent.X - Radius / FMath::Max(Scale.X, .01f)
        && FMath::Abs(Local.Y) <= HalfExtent.Y - Radius / FMath::Max(Scale.Y, .01f);
}

bool UCarnivalBumperArenaComponent::BoardPlayer(ACarnivalPlayerCharacter* Player)
{
    TArray<ACarnivalBumperCar*> Available;
    for (const auto& Car : Cars) if (IsValid(Car) && Car->CanBoard(Player)) Available.Add(Car.Get());
    Available.Sort([Player](const ACarnivalBumperCar& A, const ACarnivalBumperCar& B)
        { return FVector::DistSquared(A.GetActorLocation(), Player->GetActorLocation()) < FVector::DistSquared(B.GetActorLocation(), Player->GetActorLocation()); });
    return !Available.IsEmpty() && Available[0]->Board(Player);
}

int32 UCarnivalBumperArenaComponent::GetDriverCount() const
{
    int32 Count = 0;
    for (const auto& Car : Cars) if (IsValid(Car) && IsValid(Car->CurrentRider)) ++Count;
    return Count;
}

ACarnivalBumperCar* UCarnivalBumperArenaComponent::FindDriverCar(const AActor* Player) const
{
    for (const auto& Car : Cars) if (IsValid(Car) && Car->CurrentRider == Player) return Car.Get();
    return nullptr;
}

bool UCarnivalBumperArenaComponent::AreCarsStopped() const
{
    for (const auto& Car : Cars) if (IsValid(Car) && !Car->IsStopped()) return false;
    return true;
}

void UCarnivalBumperArenaComponent::ClearInputs()
{
    for (const auto& Car : Cars) if (IsValid(Car)) Car->ClearControlInputs();
}

bool UCarnivalBumperArenaComponent::TryUnloadAll()
{
    for (const auto& Car : Cars) if (IsValid(Car) && Car->CurrentRider) Car->TryUnload();
    return GetDriverCount() == 0;
}

void UCarnivalBumperArenaComponent::RequestDriverExit(ACarnivalPlayerCharacter* Player)
{
    if (auto* Operation = GetOperation()) Operation->RequestPassengerExit(Player);
}
