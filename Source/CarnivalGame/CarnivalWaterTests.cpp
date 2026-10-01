#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalPlayerCharacter.h"
#include "CarnivalWaterVolume.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaterSwimAndSeabedTest, "Carnival.Player.SwimAndSeabed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWaterSwimAndSeabedTest::RunTest(const FString&)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("WaterSwim"));
	UWorld* World = Instance->GetWorld();
	ON_SCOPE_EXIT { World->EndPlay(EEndPlayReason::Quit); Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	FURL URL;
	URL.AddOption(TEXT("game=/Script/Engine.GameModeBase"));
	World->SetGameMode(URL);
	World->InitializeActorsForPlay(URL);
	World->BeginPlay();

	// A 10 m deep pool: bottom at -500, surface at +500, dry ground beside it at +500.
	auto Box = [World](const FVector& Location, const FVector& Extent)
	{
		AActor* Actor = World->SpawnActor<AActor>(Location, FRotator::ZeroRotator);
		UBoxComponent* Shape = NewObject<UBoxComponent>(Actor);
		Actor->SetRootComponent(Shape);
		Shape->SetBoxExtent(Extent);
		Shape->SetCollisionProfileName(TEXT("BlockAll"));
		Shape->RegisterComponent();
		Actor->SetActorLocation(Location);
		return Actor;
	};
	Box(FVector(0.f, 0.f, -520.f), FVector(2000.f, 2000.f, 20.f));
	Box(FVector(0.f, 2600.f, 0.f), FVector(2000.f, 600.f, 500.f));
	// A jetty standing 30 cm out of the water, for climbing out.
	Box(FVector(1500.f, 0.f, 15.f), FVector(300.f, 300.f, 515.f));

	FActorSpawnParameters VolumeSpawn;
	VolumeSpawn.bDeferConstruction = true;
	ACarnivalWaterVolume* Water = World->SpawnActor<ACarnivalWaterVolume>(FVector::ZeroVector, FRotator::ZeroRotator, VolumeSpawn);
	Water->WaterExtent = FVector(2000.f, 2000.f, 500.f);
	Water->FinishSpawning(FTransform::Identity);
	TestTrue(TEXT("Water surface is the top of the box"), FMath::IsNearlyEqual(Water->GetSurfaceZ(), 500.f));
	TestTrue(TEXT("Water contains its centre"), Water->ContainsPoint(FVector(100.f, 100.f, 0.f)));
	TestFalse(TEXT("Water excludes the dry bank"), Water->ContainsPoint(FVector(0.f, 2600.f, 600.f)));
	TestTrue(TEXT("Point lookup finds the water"), ACarnivalWaterVolume::FindAt(World, FVector(0.f, 0.f, 0.f)) == Water);

	FActorSpawnParameters Spawn;
	Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACarnivalPlayerCharacter* Player = World->SpawnActor<ACarnivalPlayerCharacter>(FVector(0.f, 0.f, 900.f), FRotator::ZeroRotator, Spawn);
	UCharacterMovementComponent* Move = Player->GetCharacterMovement();
	Move->bRunPhysicsWithNoController = true;
	Move->SetMovementMode(MOVE_Falling);
	auto Run = [World](float Seconds, TFunctionRef<void()> PerFrame)
	{
		for (int32 Frame = 0; Frame < FMath::RoundToInt(Seconds * 60.f); ++Frame)
		{
			PerFrame();
			++GFrameCounter;
			World->Tick(LEVELTICK_All, 1.f / 60.f);
		}
	};

	Run(2.f, [] {});
	TestTrue(TEXT("Falling into the water starts swimming"), Move->IsSwimming() || Player->IsSeabedWalking());
	TestTrue(TEXT("The player is inside a water volume"), Player->IsInWaterVolume());

	// Dive: hold crouch until the bottom, then the player stands and walks on it.
	Player->SetSwimDownHeld(true);
	Run(6.f, [] {});
	Player->SetSwimDownHeld(false);
	Run(1.f, [] {});
	AddInfo(FString::Printf(TEXT("After dive: z=%.0f mode=%d submerged=%d seabed=%d immersion=%.2f"), Player->GetActorLocation().Z,
		static_cast<int32>(Move->MovementMode), Player->IsSubmerged(), Player->IsSeabedWalking(), Move->ImmersionDepth()));
	TestTrue(TEXT("Diving reaches the bottom"), Player->GetActorLocation().Z < -300.f);
	TestTrue(TEXT("On the bottom the player walks"), Move->IsMovingOnGround() && Player->IsSeabedWalking());
	TestTrue(TEXT("Seabed walking is slower than on land"), Move->MaxWalkSpeed <= Player->SeabedWalkSpeed + 1.f);
	const FVector Before = Player->GetActorLocation();
	Run(1.5f, [Player] { Player->AddMovementInput(FVector::ForwardVector, 1.f); });
	TestTrue(TEXT("The player walks along the bottom"), FVector::Dist2D(Before, Player->GetActorLocation()) > 150.f
		&& Move->IsMovingOnGround());

	// Swim up: hold jump to leave the bottom and rise to the surface.
	Player->SetSwimUpHeld(true);
	float Highest = Player->GetActorLocation().Z;
	Run(7.f, [Player, &Highest] { Highest = FMath::Max(Highest, Player->GetActorLocation().Z); });
	AddInfo(FString::Printf(TEXT("After rise: z=%.0f highest=%.0f mode=%d submerged=%d"), Player->GetActorLocation().Z, Highest,
		static_cast<int32>(Move->MovementMode), Player->IsSubmerged()));
	TestTrue(TEXT("Holding jump lifts off and swims up to the surface"), Highest > 400.f);
	TestTrue(TEXT("A swim loop plays while swimming"), Player->GetActiveSwimAnimation() != nullptr || !Player->GetMesh()->GetAnimInstance());
	Player->SetSwimUpHeld(false);

	// At the surface an idle swimmer floats with its head out of the water.
	Run(4.f, [] {});
	AddInfo(FString::Printf(TEXT("Floating: z=%.0f mode=%d submerged=%d"), Player->GetActorLocation().Z,
		static_cast<int32>(Move->MovementMode), Player->IsSubmerged()));
	TestTrue(TEXT("An idle swimmer at the surface stays afloat"), Player->GetActorLocation().Z > 300.f && !Player->IsSubmerged());

	// Once fully under, an idle swimmer settles back onto the bottom.
	Player->SetSwimDownHeld(true);
	Run(1.5f, [] {});
	Player->SetSwimDownHeld(false);
	Run(16.f, [] {});
	TestTrue(TEXT("An idle submerged swimmer settles onto the bottom"), Move->IsMovingOnGround() && Player->IsSeabedWalking());

	// Swimming at the surface into the jetty climbs out onto it.
	Player->SetActorLocation(FVector(700.f, 0.f, 420.f), false, nullptr, ETeleportType::TeleportPhysics);
	Move->SetMovementMode(MOVE_Swimming);
	Move->Velocity = FVector::ZeroVector;
	Run(1.f, [] {});
	// Forward is held through the climb, as a player would.
	Run(2.8f, [Player] { Player->AddMovementInput(FVector::ForwardVector, 1.f); });
	Run(1.0f, [] {});
	AddInfo(FString::Printf(TEXT("Climb out: loc=%s mode=%d"), *Player->GetActorLocation().ToString(), static_cast<int32>(Move->MovementMode)));
	TestTrue(TEXT("Swimming into a low jetty climbs out onto it"), Move->IsMovingOnGround() && Player->GetActorLocation().Z > 600.f
		&& !Player->IsInWaterVolume());

	// Walking along a floor into a flooded corridor (water to the ceiling) keeps walking through the waterline.
	Box(FVector(0.f, 6000.f, -20.f), FVector(3000.f, 400.f, 20.f));
	FActorSpawnParameters FloodSpawn;
	FloodSpawn.bDeferConstruction = true;
	ACarnivalWaterVolume* Flood = World->SpawnActor<ACarnivalWaterVolume>(FVector(1500.f, 6000.f, 300.f), FRotator::ZeroRotator, FloodSpawn);
	Flood->WaterExtent = FVector(1500.f, 400.f, 300.f);
	Flood->FinishSpawning(FTransform(FVector(1500.f, 6000.f, 300.f)));
	Player->SetActorLocation(FVector(-800.f, 6000.f, 100.f), false, nullptr, ETeleportType::TeleportPhysics);
	Move->SetMovementMode(MOVE_Falling);
	Run(0.5f, [] {});
	Run(3.f, [Player] { Player->AddMovementInput(FVector::ForwardVector, 1.f); });
	AddInfo(FString::Printf(TEXT("Flooded corridor: loc=%s mode=%d seabed=%d"), *Player->GetActorLocation().ToString(),
		static_cast<int32>(Move->MovementMode), Player->IsSeabedWalking()));
	TestTrue(TEXT("Walking into a flooded corridor keeps going on the floor"), Player->GetActorLocation().X > 200.f
		&& Move->IsMovingOnGround() && Player->IsSeabedWalking());

	// Leaving the water restores land walking speed.
	Player->SetActorLocation(FVector(0.f, 2600.f, 600.f), false, nullptr, ETeleportType::TeleportPhysics);
	Move->SetMovementMode(MOVE_Falling);
	Run(1.f, [] {});
	TestFalse(TEXT("On the bank the player is out of the water"), Player->IsInWaterVolume() || Player->IsSeabedWalking());
	TestTrue(TEXT("Land speed returns"), Move->MaxWalkSpeed > Player->SeabedWalkSpeed + 1.f);
	return true;
}
#endif
