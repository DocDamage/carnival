// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalBuildComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "DrawDebugHelpers.h"
#include "Engine/StaticMesh.h"

UCarnivalBuildComponent::UCarnivalBuildComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	bIsBuildModeActive = false;
	GridSnapSize = 100.0f;
	MaxBuildDistance = 1500.0f;
	CurrentCategoryIndex = 0;
	CurrentPieceIndex = 0;
	CurrentYawRotation = 0.0f;
	HologramComponent = nullptr;
}

void UCarnivalBuildComponent::BeginPlay()
{
	Super::BeginPlay();

	AActor* Owner = GetOwner();
	if (Owner)
	{
		HologramComponent = NewObject<UStaticMeshComponent>(Owner, TEXT("BuildHologramPreview"));
		if (HologramComponent)
		{
			HologramComponent->SetMobility(EComponentMobility::Movable);
			HologramComponent->RegisterComponent();
			HologramComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			HologramComponent->SetVisibility(false);
		}
	}
	if (bIsBuildModeActive) UpdateHologram();
}

void UCarnivalBuildComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bIsBuildModeActive)
	{
		UpdateHologram();
	}
}

void UCarnivalBuildComponent::ToggleBuildMode()
{
	bIsBuildModeActive = !bIsBuildModeActive;

	if (HologramComponent)
	{
		HologramComponent->SetVisibility(bIsBuildModeActive);
		if (bIsBuildModeActive)
		{
			UStaticMesh* Mesh = GetCurrentPieceMesh();
			if (Mesh)
			{
				HologramComponent->SetStaticMesh(Mesh);
			}
		}
	}
}

void UCarnivalBuildComponent::CyclePiece(int32 Step)
{
	if (Categories.IsValidIndex(CurrentCategoryIndex))
	{
		const TArray<UStaticMesh*>& Pieces = Categories[CurrentCategoryIndex].Pieces;
		if (Pieces.Num() > 0)
		{
			CurrentPieceIndex = ((CurrentPieceIndex + Step) % Pieces.Num() + Pieces.Num()) % Pieces.Num();
			if (HologramComponent)
			{
				HologramComponent->SetStaticMesh(Pieces[CurrentPieceIndex]);
			}
		}
	}
}

void UCarnivalBuildComponent::CycleCategory(int32 Step)
{
	if (Categories.Num() > 0)
	{
		CurrentCategoryIndex = ((CurrentCategoryIndex + Step) % Categories.Num() + Categories.Num()) % Categories.Num();
		CurrentPieceIndex = 0;
		if (HologramComponent)
		{
			UStaticMesh* Mesh = GetCurrentPieceMesh();
			HologramComponent->SetStaticMesh(Mesh);
		}
	}
}

void UCarnivalBuildComponent::RotatePiece()
{
	CurrentYawRotation = FMath::Fmod(CurrentYawRotation + 90.0f, 360.0f);
}

UStaticMesh* UCarnivalBuildComponent::GetCurrentPieceMesh() const
{
	if (Categories.IsValidIndex(CurrentCategoryIndex))
	{
		const TArray<UStaticMesh*>& Pieces = Categories[CurrentCategoryIndex].Pieces;
		if (Pieces.IsValidIndex(CurrentPieceIndex))
		{
			return Pieces[CurrentPieceIndex];
		}
	}
	return nullptr;
}

FString UCarnivalBuildComponent::GetCurrentCategoryName() const
{
	if (Categories.IsValidIndex(CurrentCategoryIndex))
	{
		return Categories[CurrentCategoryIndex].CategoryName;
	}
	return TEXT("None");
}

void UCarnivalBuildComponent::UpdateHologram()
{
	bCanPlacePiece = false;
	PlacementFeedback = TEXT("Aim at clear, level ground");
	AActor* Owner = GetOwner();
	if (!Owner || !HologramComponent)
	{
		return;
	}
	UStaticMesh* Mesh = GetCurrentPieceMesh();
	HologramComponent->SetStaticMesh(Mesh);
	HologramComponent->SetVisibility(bIsBuildModeActive && Mesh != nullptr);
	if (!Mesh)
	{
		PlacementFeedback = TEXT("No building piece selected");
		return;
	}

	FVector TraceStart = Owner->GetActorLocation() + FVector(0.0f, 0.0f, 40.0f);
	FVector Forward = Owner->GetActorForwardVector();

	ACharacter* Char = Cast<ACharacter>(Owner);
	if (Char && Char->GetController())
	{
		FRotator ViewRot = Char->GetController()->GetControlRotation();
		Forward = ViewRot.Vector();
		TraceStart = Owner->GetActorLocation() + FVector(0.0f, 0.0f, 60.0f);
	}

	FVector TraceEnd = TraceStart + Forward * MaxBuildDistance;

	FHitResult Hit;
	FCollisionQueryParams Params;
	Params.AddIgnoredActor(Owner);

	if (!GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params)
		|| Hit.ImpactNormal.Z < .7f) return;
	FVector TargetLocation = Hit.ImpactPoint;

	// Snap to grid
	if (GridSnapSize > 0.0f)
	{
		TargetLocation.X = FMath::GridSnap(TargetLocation.X, GridSnapSize);
		TargetLocation.Y = FMath::GridSnap(TargetLocation.Y, GridSnapSize);
	}
	// Recheck support after XY snapping so a preview cannot straddle a cliff at the old height.
	FHitResult Support;
	if (!GetWorld()->LineTraceSingleByChannel(Support, TargetLocation + FVector(0, 0, 100),
		TargetLocation - FVector(0, 0, 150), ECC_Visibility, Params) || Support.ImpactNormal.Z < .7f) return;
	const FBox Bounds = Mesh->GetBoundingBox();
	TargetLocation.Z = Support.ImpactPoint.Z - Bounds.Min.Z + 2.f;

	FRotator TargetRotation(0.0f, CurrentYawRotation, 0.0f);
	CurrentHologramTransform = FTransform(TargetRotation, TargetLocation, FVector(1.0f));

	HologramComponent->SetWorldTransform(CurrentHologramTransform);
	const FVector Center = CurrentHologramTransform.TransformPosition(Bounds.GetCenter());
	const FVector Extent = (Bounds.GetExtent() - FVector(1.f)).ComponentMax(FVector(1.f));
	FCollisionQueryParams ClearanceParams(SCENE_QUERY_STAT(CarnivalBuildClearance), false);
	// Include the player capsule: building must never trap its owner inside a newly placed piece.
	bCanPlacePiece = FVector::DistSquared(Owner->GetActorLocation(), Center) <= FMath::Square(MaxBuildDistance)
		&& !GetWorld()->OverlapBlockingTestByProfile(Center, TargetRotation.Quaternion(), TEXT("BlockAll"),
			FCollisionShape::MakeBox(Extent), ClearanceParams);
	PlacementFeedback = bCanPlacePiece ? TEXT("Ready to place") : TEXT("Space is blocked or out of reach");
}

bool UCarnivalBuildComponent::PlacePiece()
{
	if (!bIsBuildModeActive)
	{
		return false;
	}
	UpdateHologram();
	if (!bCanPlacePiece) return false;

	UStaticMesh* MeshToSpawn = GetCurrentPieceMesh();
	if (!MeshToSpawn)
	{
		return false;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AStaticMeshActor* PlacedActor = GetWorld()->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(),
		CurrentHologramTransform,
		SpawnParams
	);

	if (PlacedActor && PlacedActor->GetStaticMeshComponent())
	{
		PlacedActor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
		PlacedActor->GetStaticMeshComponent()->SetStaticMesh(MeshToSpawn);
		PlacedActor->GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));
		PlacedBuildingActors.Add(PlacedActor);
		return true;
	}

	return false;
}

bool UCarnivalBuildComponent::DemolishPiece()
{
	if (!bIsBuildModeActive)
	{
		return false;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return false;
	}

	FVector TraceStart = Owner->GetActorLocation() + FVector(0.0f, 0.0f, 60.0f);
	FVector Forward = Owner->GetActorForwardVector();

	ACharacter* Char = Cast<ACharacter>(Owner);
	if (Char && Char->GetController())
	{
		Forward = Char->GetController()->GetControlRotation().Vector();
	}

	FVector TraceEnd = TraceStart + Forward * MaxBuildDistance;

	FHitResult Hit;
	FCollisionQueryParams Params;
	Params.AddIgnoredActor(Owner);

	if (GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
	{
		AActor* HitActor = Hit.GetActor();
		if (HitActor && PlacedBuildingActors.Contains(HitActor))
		{
			PlacedBuildingActors.Remove(HitActor);
			HitActor->Destroy();
			return true;
		}
	}

	return false;
}
