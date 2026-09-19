// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalBuildComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "DrawDebugHelpers.h"

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
			HologramComponent->RegisterComponent();
			HologramComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			HologramComponent->SetVisibility(false);
		}
	}
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
			CurrentPieceIndex = (CurrentPieceIndex + Step + Pieces.Num()) % Pieces.Num();
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
		CurrentCategoryIndex = (CurrentCategoryIndex + Step + Categories.Num()) % Categories.Num();
		CurrentPieceIndex = 0;
		if (HologramComponent)
		{
			UStaticMesh* Mesh = GetCurrentPieceMesh();
			if (Mesh)
			{
				HologramComponent->SetStaticMesh(Mesh);
			}
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
	AActor* Owner = GetOwner();
	if (!Owner || !HologramComponent)
	{
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

	FVector TargetLocation = TraceEnd;
	if (GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_WorldStatic, Params))
	{
		TargetLocation = Hit.ImpactPoint;
	}

	// Snap to grid
	if (GridSnapSize > 0.0f)
	{
		TargetLocation.X = FMath::GridSnap(TargetLocation.X, GridSnapSize);
		TargetLocation.Y = FMath::GridSnap(TargetLocation.Y, GridSnapSize);
		TargetLocation.Z = FMath::GridSnap(TargetLocation.Z, 50.0f); // 50cm vertical snap
	}

	FRotator TargetRotation(0.0f, CurrentYawRotation, 0.0f);
	CurrentHologramTransform = FTransform(TargetRotation, TargetLocation, FVector(1.0f));

	HologramComponent->SetWorldTransform(CurrentHologramTransform);
}

bool UCarnivalBuildComponent::PlacePiece()
{
	if (!bIsBuildModeActive)
	{
		return false;
	}

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
		PlacedActor->GetStaticMeshComponent()->SetStaticMesh(MeshToSpawn);
		PlacedActor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
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

	if (GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_WorldDynamic, Params) ||
		GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_WorldStatic, Params))
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

