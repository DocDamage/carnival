#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerSafeRecoveryTest, "Carnival.Player.SafeRecovery",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerSafeRecoveryTest::RunTest(const FString&)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("PlayerSafeRecovery"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL);
	World->InitializeActorsForPlay(URL);
	World->BeginPlay();

	AActor* Floor = World->SpawnActor<AActor>(FVector(0.f, 0.f, -20.f), FRotator::ZeroRotator);
	UBoxComponent* FloorBox = NewObject<UBoxComponent>(Floor);
	Floor->SetRootComponent(FloorBox);
	FloorBox->SetBoxExtent(FVector(1000.f, 1000.f, 20.f));
	FloorBox->SetCollisionProfileName(TEXT("BlockAll"));
	FloorBox->RegisterComponent();

	FActorSpawnParameters Spawn;
	Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACarnivalPlayerCharacter* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0.f, 0.f, 98.f), FRotator::ZeroRotator, Spawn);
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	Player->Tick(1.f / 60.f);
	TestFalse(TEXT("Recovery is hidden during ordinary play"), Player->CanRecoverToSafePosition());

	Player->SetActorLocation(FVector(0.f, 0.f, 900.f), false, nullptr, ETeleportType::TeleportPhysics);
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	for (int32 Frame = 0; Frame < 310; ++Frame) Player->Tick(1.f / 60.f);
	TestTrue(TEXT("A sustained fall exposes safe recovery"), Player->CanRecoverToSafePosition());
	TestTrue(TEXT("Falling player returns to a clear point on the saved floor"), Player->TryRecoverToSafePosition());
	AddInfo(FString::Printf(TEXT("After fall recovery: location=%s mode=%d collision=%d"),
		*Player->GetActorLocation().ToString(), static_cast<int32>(Player->GetCharacterMovement()->MovementMode),
		static_cast<int32>(Player->GetCapsuleComponent()->GetCollisionEnabled())));
	TestTrue(TEXT("Recovery restores walking movement"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking);
	TestTrue(TEXT("Recovery restores capsule collision"), Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
	FHitResult RestoredFloor;
	const float RestoredHalfHeight = Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const bool bRestoredToWalkableFloor = World->LineTraceSingleByChannel(RestoredFloor,
		Player->GetActorLocation() - FVector(0.f, 0.f, RestoredHalfHeight - 10.f),
		Player->GetActorLocation() - FVector(0.f, 0.f, RestoredHalfHeight + 20.f), ECC_Visibility)
		&& RestoredFloor.ImpactNormal.Z >= Player->GetCharacterMovement()->GetWalkableFloorZ();
	TestTrue(TEXT("Recovery places the capsule just above the saved walkable floor"), bRestoredToWalkableFloor
		&& FMath::IsNearlyEqual(Player->GetActorLocation().Z - RestoredFloor.ImpactPoint.Z - RestoredHalfHeight, 2.f, 2.5f));

	Player->GetCharacterMovement()->SetMovementMode(MOVE_Swimming);
	for (int32 Frame = 0; Frame < 250; ++Frame) Player->Tick(1.f / 60.f);
	TestTrue(TEXT("A sustained swim exposes recovery from water"), Player->CanRecoverToSafePosition());
	TestTrue(TEXT("Swimming player can recover without losing the possessed character"), Player->TryRecoverToSafePosition());
	TestTrue(TEXT("Water recovery restores ground movement"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking
		&& Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);

	AActor* Wall = World->SpawnActor<AActor>(FVector(60.f, 0.f, 120.f), FRotator::ZeroRotator);
	UBoxComponent* WallBox = NewObject<UBoxComponent>(Wall);
	Wall->SetRootComponent(WallBox);
	WallBox->SetBoxExtent(FVector(10.f, 200.f, 100.f));
	WallBox->SetCollisionProfileName(TEXT("BlockAll"));
	WallBox->RegisterComponent();
	for (int32 Frame = 0; Frame < 330; ++Frame)
	{
		Player->AddMovementInput(FVector::ForwardVector, 1.f);
		++GFrameCounter;
		World->Tick(LEVELTICK_All, 1.f / 60.f);
	}
	TestTrue(TEXT("Sustained input against a blocked path exposes recovery"), Player->CanRecoverToSafePosition());
	TestTrue(TEXT("Stuck player can return to the last clear walkable point"), Player->TryRecoverToSafePosition());
	TestTrue(TEXT("Blocked-path recovery preserves walking and collision"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking
		&& Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);

	// A walkable pit refreshes the safe point on its own floor, so ordinary recovery stays inside.
	auto Box = [World](const FVector& Location, const FVector& Extent)
	{
		AActor* Actor = World->SpawnActor<AActor>(Location, FRotator::ZeroRotator);
		UBoxComponent* Shape = NewObject<UBoxComponent>(Actor);
		Actor->SetRootComponent(Shape); Shape->SetBoxExtent(Extent); Shape->SetCollisionProfileName(TEXT("BlockAll")); Shape->RegisterComponent();
		Actor->SetActorLocation(Location);   // a root attached after spawning starts at the origin
		return Actor;
	};
	Wall->Destroy();
	const FVector Pit(4000.f, 0.f, -2000.f);
	Box(Pit + FVector(0.f, 0.f, -20.f), FVector(300.f, 300.f, 20.f));
	for (const FVector& Side : {FVector(320.f, 0.f, 0.f), FVector(-320.f, 0.f, 0.f), FVector(0.f, 320.f, 0.f), FVector(0.f, -320.f, 0.f)})
		Box(Pit + Side + FVector(0.f, 0.f, 600.f), FVector(Side.X != 0.f ? 20.f : 340.f, Side.Y != 0.f ? 20.f : 340.f, 600.f));
	Player->SetActorLocation(Pit + FVector(0.f, 0.f, 98.f), false, nullptr, ETeleportType::TeleportPhysics);
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	for (int32 Frame = 0; Frame < 30; ++Frame) Player->Tick(1.f / 60.f);
	TestFalse(TEXT("Without route anchors there is nowhere to return to"), Player->ReturnToNearestRoute());

	auto Anchor = [World](const FVector& Location)
	{
		AActor* Actor = World->SpawnActor<AActor>(Location, FRotator(0.f, 90.f, 0.f));
		USceneComponent* Root = NewObject<USceneComponent>(Actor);
		Actor->SetRootComponent(Root); Root->RegisterComponent(); Actor->SetActorLocation(Location);
		Actor->Tags.Add(ACarnivalPlayerCharacter::RouteAnchorTag);
		return Actor;
	};
	Box(FVector(300.f, 300.f, 120.f), FVector(150.f, 150.f, 100.f));   // occupies the nearer anchor
	Anchor(FVector(300.f, 300.f, 98.f));
	AActor* Clear = Anchor(FVector(-500.f, -500.f, 98.f));
	TestTrue(TEXT("Trapped player returns to a route anchor"), Player->ReturnToNearestRoute());
	AddInfo(FString::Printf(TEXT("Return to path: player=%s clear anchor=%s"), *Player->GetActorLocation().ToString(), *Clear->GetActorLocation().ToString()));
	TestTrue(TEXT("A blocked anchor is skipped for the next clear one"),
		FVector::Dist2D(Player->GetActorLocation(), Clear->GetActorLocation()) < 220.f);
	TestTrue(TEXT("Return to path leaves walking movement and collision"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking
		&& Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
	TestFalse(TEXT("Return to path clears pending recovery"), Player->CanRecoverToSafePosition());

	// Fall net: a short drop is left alone; a deep fall below the last safe point recovers on its own.
	for (int32 Frame = 0; Frame < 30; ++Frame) Player->Tick(1.f / 60.f);   // refresh the safe point at the anchor
	const FVector SafeSpot = Player->GetActorLocation();
	Player->SetActorLocation(SafeSpot - FVector(0.f, 0.f, 1600.f), false, nullptr, ETeleportType::TeleportPhysics);
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	Player->Tick(1.f / 60.f);
	TestTrue(TEXT("A 16 m drop does not trigger the fall net"), Player->GetCharacterMovement()->MovementMode == MOVE_Falling
		&& Player->GetActorLocation().Z < SafeSpot.Z - 1000.f);
	Player->SetActorLocation(SafeSpot - FVector(0.f, 0.f, 4500.f), false, nullptr, ETeleportType::TeleportPhysics);
	Player->Tick(1.f / 60.f);
	AddInfo(FString::Printf(TEXT("Fall net: safe=%s after=%s"), *SafeSpot.ToString(), *Player->GetActorLocation().ToString()));
	TestTrue(TEXT("A 45 m fall returns the player to the last safe point"), FVector::Dist(Player->GetActorLocation(), SafeSpot) < 220.f);
	TestTrue(TEXT("The fall net leaves walking movement and collision"), Player->GetCharacterMovement()->MovementMode == MOVE_Walking
		&& Player->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
	return true;
}
#endif
