// Copyright CarnivalMetaHuman. All Rights Reserved.
#include "CarnivalSaveSubsystem.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalMissionInteractionActor.h"
#include "CarnivalActivityBase.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "EngineUtils.h"
#include "Misc/PackageName.h"

namespace
{
FString MapId(const UWorld* World)
{
	FString Package = World->GetOutermost()->GetName();
	const FString Prefix = World->StreamingLevelsPrefix;
	if (!Prefix.IsEmpty()) Package.ReplaceInline(*Prefix, TEXT(""));
	return Package;
}
FString DoorId(const AActor* Actor)
{
	FString Package = Actor->GetLevel()->GetOutermost()->GetName();
	const FString Prefix = Actor->GetWorld()->StreamingLevelsPrefix;
	if (!Prefix.IsEmpty()) Package.ReplaceInline(*Prefix, TEXT(""));
	return Package + TEXT(":") + Actor->GetName();
}
}

bool UCarnivalSaveGame::IsValidSnapshot() const
{
	if (Version < 1 || Version > 3 || Generation <= 0 || Generation == MAX_int64 || !FPackageName::IsValidLongPackageName(MapPackage, true)
		|| !PlayerTransform.IsValid() || !PlayerTransform.GetScale3D().Equals(FVector::OneVector)
		|| ViewRotation.ContainsNaN() || !UCarnivalMissionSubsystem::IsSaveableState(MissionState)
		|| Buildings.Num() > 2000 || Doors.Num() > 256) return false;
	FCarnivalCampaignSnapshot Migrated;
	if (Version == 3 && !UCarnivalCampaignSubsystem::IsValidSnapshot(Campaign)) return false;
	if (Version == 2 && !UCarnivalCampaignSubsystem::MigrateVersion2(Campaign, Migrated)) return false;
	TSet<FString> Ids;
	for (const auto& Door : Doors)
	{
		if (Door.ActorId.IsEmpty() || Ids.Contains(Door.ActorId)
			|| (Door.bOpen && MissionState < ECarnivalStoryMissionState::FindWorker)) return false;
		Ids.Add(Door.ActorId);
	}
	for (const auto& Building : Buildings)
		if (!Building.Mesh.IsValid() || !Building.Transform.IsValid()
			|| !Building.Transform.GetScale3D().Equals(FVector::OneVector)) return false;
	return true;
}

FString UCarnivalSaveSubsystem::BankName(int32 Slot, int32 Bank) const
{
	return FString::Printf(TEXT("%s%d_%d"), *SlotPrefix, Slot + 1, Bank);
}

UCarnivalSaveGame* UCarnivalSaveSubsystem::ReadLatest(int32 Slot, int32& Bank) const
{
	Bank = INDEX_NONE;
	if (Slot < 0 || Slot >= SlotCount) return nullptr;
	UCarnivalSaveGame* Latest = nullptr;
	for (int32 Index = 0; Index < 2; ++Index)
	{
		const FString Name = BankName(Slot, Index);
		if (!UGameplayStatics::DoesSaveGameExist(Name, 0)) continue;
		auto* Candidate = Cast<UCarnivalSaveGame>(UGameplayStatics::LoadGameFromSlot(Name, 0));
		if (Candidate && Candidate->IsValidSnapshot() && (!Latest || Candidate->Generation > Latest->Generation))
		{
			Latest = Candidate;
			Bank = Index;
		}
	}
	return Latest;
}

bool UCarnivalSaveSubsystem::CheckPlayer(ACarnivalPlayerCharacter* Player)
{
	if (!IsValid(Player) || !Player->GetController() || Player->GetWorld() != GetWorld()
		|| !Player->BuildComponent || Player->MountedMotorcycle || Player->MountedBoat || Player->MountedHovercraft
		|| Player->IsUsingRide() || Player->IsParkourTraversing() || Player->ActiveActivity
		|| Player->bIsCrouched || !Player->GetCharacterMovement()->IsMovingOnGround()
		|| (Player->LocomotionState != ECarnivalLocomotionState::Walking
			&& Player->LocomotionState != ECarnivalLocomotionState::Jogging
			&& Player->LocomotionState != ECarnivalLocomotionState::Sprinting))
	{
		LastResult = TEXT("Stand on safe ground and finish the current ride, vehicle or activity first.");
		return false;
	}
	const auto* Mission = GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>();
	if (!Mission || !UCarnivalMissionSubsystem::IsSaveableState(Mission->GetMissionState()))
	{
		LastResult = TEXT("Wait for the doll encounter to finish.");
		return false;
	}
	FCollisionQueryParams Query(SCENE_QUERY_STAT(CarnivalSaveGround), false, Player);
	for (AActor* Actor : Player->BuildComponent->GetPlacedBuildingActors()) if (IsValid(Actor)) Query.AddIgnoredActor(Actor);
	FHitResult Floor;
	if (!GetWorld()->LineTraceSingleByChannel(Floor, Player->GetActorLocation(),
		Player->GetActorLocation() - FVector(0, 0, Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 15.f), ECC_Visibility, Query)
		|| !Player->GetCharacterMovement()->IsWalkable(Floor))
	{
		LastResult = TEXT("Stand on permanent, safe ground before saving or loading.");
		return false;
	}
	return true;
}

bool UCarnivalSaveSubsystem::SaveSlot(int32 Slot, ACarnivalPlayerCharacter* Player)
{
	if (Slot < 0 || Slot >= SlotCount) { LastResult = TEXT("Invalid save slot."); return false; }
	if (!CheckPlayer(Player)) return false;
	int32 Bank;
	const auto* Previous = ReadLatest(Slot, Bank);
	auto* Saved = NewObject<UCarnivalSaveGame>();
	Saved->Generation = Previous ? Previous->Generation + 1 : 1;
	Saved->SavedUtc = FDateTime::UtcNow();
	Saved->MapPackage = MapId(GetWorld());
	Saved->PlayerTransform = Player->GetActorTransform();
	Saved->ViewRotation = Player->GetController()->GetControlRotation();
	Saved->MissionState = GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>()->GetMissionState();
	Saved->Campaign = GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>()->Capture();
	Saved->Buildings = Player->BuildComponent->CaptureBuildings();
	for (TActorIterator<ACarnivalMissionInteractionActor> It(GetWorld()); It; ++It)
	{
		if (It->Interaction != ECarnivalMissionInteraction::MusicRoomDoor) continue;
		auto& Door = Saved->Doors.AddDefaulted_GetRef();
		Door.ActorId = DoorId(*It);
		Door.bOpen = It->IsSavedDoorOpen();
	}
	// Write only the older bank. A failed/interrupted write leaves the current bank intact.
	const FString Name = BankName(Slot, Bank == 0 ? 1 : 0);
	if (!Saved->IsValidSnapshot() || !UGameplayStatics::SaveGameToSlot(Saved, Name, 0))
	{
		LastResult = TEXT("Save failed. The previous save was kept.");
		return false;
	}
	const auto* Check = Cast<UCarnivalSaveGame>(UGameplayStatics::LoadGameFromSlot(Name, 0));
	if (!Check || !Check->IsValidSnapshot() || Check->Generation != Saved->Generation)
	{
		UGameplayStatics::DeleteGameInSlot(Name, 0);
		LastResult = TEXT("Save verification failed. The previous save was kept.");
		return false;
	}
	LastResult = FString::Printf(TEXT("Saved to slot %d."), Slot + 1);
	return true;
}

bool UCarnivalSaveSubsystem::LoadSlot(int32 Slot, ACarnivalPlayerCharacter* Player)
{
	if (Slot < 0 || Slot >= SlotCount) { LastResult = TEXT("Invalid save slot."); return false; }
	if (!CheckPlayer(Player)) return false;
	int32 Bank;
	const auto* Saved = ReadLatest(Slot, Bank);
	if (!Saved) { LastResult = TEXT("This slot has no compatible save."); return false; }
	// Legacy slots keep their original story, buildings, doors and position. Version-1
	// inventory starts empty, with the sequel unlocked if Eli was rescued; version-2
	// progress maps onto the current, shorter station chain.
	FCarnivalCampaignSnapshot Campaign = Saved->Version == 3 ? Saved->Campaign : FCarnivalCampaignSnapshot();
	if (Saved->Version == 1) Campaign.bUnlocked = Saved->MissionState == ECarnivalStoryMissionState::Complete;
	if (Saved->Version == 2 && !UCarnivalCampaignSubsystem::MigrateVersion2(Saved->Campaign, Campaign))
	{ LastResult = TEXT("Saved campaign data is invalid."); return false; }
	if (!UCarnivalCampaignSubsystem::IsValidSnapshot(Campaign)) { LastResult = TEXT("Saved campaign data is invalid."); return false; }
	if (Saved->MapPackage != MapId(GetWorld()))
	{
		LastResult = TEXT("Open the saved location before loading this slot.");
		return false;
	}
	TMap<FString, ACarnivalMissionInteractionActor*> Doors;
	for (TActorIterator<ACarnivalMissionInteractionActor> It(GetWorld()); It; ++It)
		if (It->Interaction == ECarnivalMissionInteraction::MusicRoomDoor) Doors.Add(DoorId(*It), *It);
	if (Doors.Num() != Saved->Doors.Num()) { LastResult = TEXT("Wait for the saved rooms to finish loading."); return false; }
	for (const auto& Door : Saved->Doors)
		if (!Doors.Contains(Door.ActorId)) { LastResult = TEXT("A saved door is unavailable."); return false; }
	FCollisionQueryParams Query(SCENE_QUERY_STAT(CarnivalLoadPlayer), false, Player);
	for (AActor* Actor : Player->BuildComponent->GetPlacedBuildingActors()) if (IsValid(Actor)) Query.AddIgnoredActor(Actor);
	// Inspect the saved door poses before committing anything. Always roll back this
	// temporary preflight, including on an unsafe player/building result.
	TMap<ACarnivalMissionInteractionActor*, bool> PreviousDoors;
	for (const auto& Door : Saved->Doors)
	{
		auto* Actor = Doors[Door.ActorId];
		PreviousDoors.Add(Actor, Actor->IsSavedDoorOpen());
		if (!Actor->RestoreSavedDoor(Door.bOpen))
		{
			for (const auto& Previous : PreviousDoors) Previous.Key->RestoreSavedDoor(Previous.Value);
			LastResult = TEXT("Wait for the saved door components to finish loading.");
			return false;
		}
	}
	const FVector Location = Saved->PlayerTransform.GetLocation();
	const auto* Capsule = Player->GetCapsuleComponent();
	FHitResult Floor;
	const float HalfHeight = Capsule->GetScaledCapsuleHalfHeight();
	const bool bGround = GetWorld()->LineTraceSingleByChannel(Floor, Location,
		Location - FVector(0, 0, HalfHeight + 15.f), ECC_Visibility, Query)
		&& Player->GetCharacterMovement()->IsWalkable(Floor);
	const bool bBlocked = GetWorld()->OverlapBlockingTestByProfile(Location, Saved->PlayerTransform.GetRotation(),
		Capsule->GetCollisionProfileName(), FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(), HalfHeight - 1.f), Query);
	if (!bGround || bBlocked)
	{
		for (const auto& Previous : PreviousDoors) Previous.Key->RestoreSavedDoor(Previous.Value);
		LastResult = TEXT("The saved position is blocked or lacks safe ground. Your current game was kept.");
		return false;
	}
	if (!Player->BuildComponent->RestoreBuildings(Saved->Buildings, Location, LastResult))
	{
		for (const auto& Previous : PreviousDoors) Previous.Key->RestoreSavedDoor(Previous.Value);
		return false;
	}
	Player->StopSprinting();
	Player->StopJumping();
	Player->ConsumeMovementInputVector();
	Player->GetCharacterMovement()->StopMovementImmediately();
	Player->SetActorTransform(Saved->PlayerTransform, false, nullptr, ETeleportType::TeleportPhysics);
	Player->GetController()->SetControlRotation(Saved->ViewRotation);
	Player->ResetRecoveryAfterLoad();
	GetGameInstance()->GetSubsystem<UCarnivalCampaignSubsystem>()->Restore(Campaign);
	GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>()->RestoreSavedState(Saved->MissionState);
	for (const auto& Door : Saved->Doors) Doors[Door.ActorId]->RestoreSavedDoor(Door.bOpen);
	LastResult = FString::Printf(TEXT("Loaded slot %d."), Slot + 1);
	return true;
}

FString UCarnivalSaveSubsystem::GetSlotSummary(int32 Slot) const
{
	int32 Bank;
	const auto* Saved = ReadLatest(Slot, Bank);
	if (!Saved) return TEXT("Empty or incompatible");
	return Saved->SavedUtc.ToString(TEXT("%Y-%m-%d %H:%M UTC"));
}
