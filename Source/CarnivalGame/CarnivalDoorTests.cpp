#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalDoorSubsystem.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVendorDoorInteractionTest, "Carnival.World.VendorDoors",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
	TArray<UStaticMeshComponent*> DoorLeaves(AActor* Door)
	{
		TArray<UStaticMeshComponent*> Meshes, Leaves;
		Door->GetComponents<UStaticMeshComponent>(Meshes);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			const FString Name = Mesh->GetStaticMesh() ? Mesh->GetStaticMesh()->GetName() : FString();
			if (Name.Contains(TEXT("Door_Plate")) || Name == TEXT("SM_Door02_D") || Name == TEXT("SM_Door02_E")) Leaves.Add(Mesh);
		}
		return Leaves;
	}
}

bool FVendorDoorInteractionTest::RunTest(const FString&)
{
	UClass* HospitalDoor = LoadClass<AActor>(nullptr, TEXT("/Game/Hospital_Meshingun/Blueprint/Prefab/BP_Door_01a.BP_Door_01a_C"));
	UClass* MansionDoor = LoadClass<AActor>(nullptr, TEXT("/Game/Mansion/Mesh/Assets/Doors/BP_Door02.BP_Door02_C"));
	if (!TestNotNull(TEXT("Hospital door class loads"), HospitalDoor) || !TestNotNull(TEXT("Mansion door class loads"), MansionDoor)) return false;

	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("VendorDoors"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL);
	World->InitializeActorsForPlay(URL);
	World->BeginPlay();
	UCarnivalDoorSubsystem* Doors = World->GetSubsystem<UCarnivalDoorSubsystem>();
	if (!TestNotNull(TEXT("Door subsystem exists"), Doors)) return false;

	for (UClass* DoorClass : { HospitalDoor, MansionDoor })
	{
		const FVector Origin(DoorClass == HospitalDoor ? 0.f : 2000.f, 0.f, 0.f);
		AActor* Door = World->SpawnActor<AActor>(DoorClass, Origin, FRotator::ZeroRotator);
		if (!TestNotNull(TEXT("Door spawns"), Door)) continue;
		TArray<UStaticMeshComponent*> Leaves = DoorLeaves(Door);
		TestTrue(*FString::Printf(TEXT("%s has door leaves"), *DoorClass->GetName()), Leaves.Num() > 0);
		TestFalse(TEXT("Door starts closed"), Doors->IsDoorOpen(Door));

		const FBox LeafBox = Leaves[0]->Bounds.GetBox();
		// Stand on one side of the doorway, along its thin axis.
		const FVector Extent = LeafBox.GetExtent();
		const FVector Side = Extent.X < Extent.Y ? FVector(140.f, 0.f, 0.f) : FVector(0.f, 140.f, 0.f);
		const FVector From = LeafBox.GetCenter() + Side;
		TestTrue(TEXT("The door is found from beside it"), Doors->FindDoorNear(From) == Door);
		TestTrue(TEXT("The door is not found from far away"), Doors->FindDoorNear(From + Side * 10.f) == nullptr);

		const float ClosedDistance = FVector::Dist2D(Leaves[0]->Bounds.Origin, From);
		TestTrue(TEXT("Closed door opens"), Doors->ToggleDoor(Door, From, true));
		TestTrue(TEXT("Door reports open"), Doors->IsDoorOpen(Door));
		for (UStaticMeshComponent* Leaf : Leaves)
		{
			TestTrue(TEXT("Leaf becomes movable"), Leaf->Mobility == EComponentMobility::Movable);
			TestTrue(TEXT("Leaf swings a quarter turn"), FMath::IsNearlyEqual(FMath::Abs(FRotator::NormalizeAxis(Leaf->GetRelativeRotation().Yaw)), 90.f, 0.5f));
		}
		TestTrue(TEXT("Leaf swings away from the player"), FVector::Dist2D(Leaves[0]->Bounds.Origin, From) > ClosedDistance);

		TestTrue(TEXT("Open door closes"), Doors->ToggleDoor(Door, From, true));
		TestFalse(TEXT("Door reports closed"), Doors->IsDoorOpen(Door));
		for (UStaticMeshComponent* Leaf : Leaves)
		{
			TestTrue(TEXT("Leaf returns to the frame"), FMath::IsNearlyZero(FRotator::NormalizeAxis(Leaf->GetRelativeRotation().Yaw), 0.5f));
		}
	}

	// The player's context interact opens the door it stands beside, animating over a short time.
	AActor* Door = World->SpawnActor<AActor>(HospitalDoor, FVector(0.f, 3000.f, 0.f), FRotator::ZeroRotator);
	const FBox LeafBox = DoorLeaves(Door)[0]->Bounds.GetBox();
	const FVector Extent = LeafBox.GetExtent();
	const FVector Side = Extent.X < Extent.Y ? FVector(120.f, 0.f, 0.f) : FVector(0.f, 120.f, 0.f);
	FActorSpawnParameters Spawn;
	Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACarnivalPlayerCharacter* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(LeafBox.GetCenter().X, LeafBox.GetCenter().Y, 98.f) + Side, FRotator::ZeroRotator, Spawn);
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	TestTrue(TEXT("Player sees the door"), Player->FindNearbyDoor() == Door);
	Player->TryContextInteract();
	TestTrue(TEXT("Interact opens the door"), Doors->IsDoorOpen(Door));
	for (int32 Frame = 0; Frame < 60; ++Frame) Doors->Tick(1.f / 60.f);
	TestTrue(TEXT("Door finishes its swing"), FMath::IsNearlyEqual(FMath::Abs(FRotator::NormalizeAxis(DoorLeaves(Door)[0]->GetRelativeRotation().Yaw)), 90.f, 0.5f));
	Player->TryContextInteract();
	TestFalse(TEXT("Interact again closes it"), Doors->IsDoorOpen(Door));

	// A double door authored with one leaf ajar counts as closed, so the first interact opens it fully.
	UClass* DoubleDoor = LoadClass<AActor>(nullptr, TEXT("/Game/Hospital_Meshingun/Blueprint/Prefab/BP_Door_02a.BP_Door_02a_C"));
	if (TestNotNull(TEXT("Hospital double door class loads"), DoubleDoor))
	{
		AActor* Ajar = World->SpawnActor<AActor>(DoubleDoor, FVector(0.f, 9000.f, 0.f), FRotator::ZeroRotator);
		TArray<UStaticMeshComponent*> AjarLeaves = DoorLeaves(Ajar);
		if (TestEqual(TEXT("Double door has two leaves"), AjarLeaves.Num(), 2))
		{
			AjarLeaves[1]->SetMobility(EComponentMobility::Movable);
			AjarLeaves[1]->SetRelativeRotation(FRotator(0.f, 170.f, 0.f));
			TestFalse(TEXT("A door with one leaf ajar is not open"), Doors->IsDoorOpen(Ajar));
			const FBox AjarBox = AjarLeaves[0]->Bounds.GetBox();
			const FVector AjarSide = AjarBox.GetExtent().X < AjarBox.GetExtent().Y ? FVector(140.f, 0.f, 0.f) : FVector(0.f, 140.f, 0.f);
			TestTrue(TEXT("Interacting with an ajar door opens it"), Doors->ToggleDoor(Ajar, AjarBox.GetCenter() + AjarSide, true));
			TestTrue(TEXT("The ajar door is now open"), Doors->IsDoorOpen(Ajar));
			for (UStaticMeshComponent* Leaf : AjarLeaves)
			{
				TestTrue(TEXT("Every leaf ends a quarter turn open"), FMath::IsNearlyEqual(FMath::Abs(FRotator::NormalizeAxis(Leaf->GetRelativeRotation().Yaw)), 90.f, 0.5f));
			}
		}
	}

	// A sealed door (one that leads into a wall or out of the demo) is never offered and never opens.
	AActor* Sealed = World->SpawnActor<AActor>(HospitalDoor, FVector(0.f, 6000.f, 0.f), FRotator::ZeroRotator);
	Sealed->Tags.Add(UCarnivalDoorSubsystem::SealedDoorTag);
	const FBox SealedBox = DoorLeaves(Sealed)[0]->Bounds.GetBox();
	const FVector SealedSide = SealedBox.GetExtent().X < SealedBox.GetExtent().Y ? FVector(140.f, 0.f, 0.f) : FVector(0.f, 140.f, 0.f);
	TestTrue(TEXT("A sealed door is not found"), Doors->FindDoorNear(SealedBox.GetCenter() + SealedSide) == nullptr);
	TestFalse(TEXT("A sealed door does not toggle"), Doors->ToggleDoor(Sealed, SealedBox.GetCenter() + SealedSide, true));
	TestFalse(TEXT("A sealed door stays closed"), Doors->IsDoorOpen(Sealed));
	TestTrue(TEXT("A sealed door is found for the Locked prompt"), Doors->FindDoorNear(SealedBox.GetCenter() + SealedSide, 220.f, true) == Sealed);
	TestTrue(TEXT("An ordinary door is not reported as locked"), Doors->FindDoorNear(LeafBox.GetCenter() + Side, 220.f, true) == nullptr);
	return true;
}
#endif
