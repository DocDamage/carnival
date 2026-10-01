// Copyright CarnivalMetaHuman. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CarnivalBuildComponent.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;

USTRUCT()
struct FCarnivalSavedBuilding
{
	GENERATED_BODY()
	UPROPERTY(SaveGame) FSoftObjectPath Mesh;
	UPROPERTY(SaveGame) FTransform Transform;
};

USTRUCT(BlueprintType)
struct FCarnivalBuildCategory
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build")
	FString CategoryName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build")
	TArray<UStaticMesh*> Pieces;
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent), Blueprintable)
class CARNIVALGAME_API UCarnivalBuildComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	TArray<FCarnivalSavedBuilding> CaptureBuildings() const;
	// Validate and stage all replacements before discarding any current construction.
	bool RestoreBuildings(const TArray<FCarnivalSavedBuilding>& Buildings, const FVector& PlayerLocation, FString& Error);
	const TArray<AActor*>& GetPlacedBuildingActors() const { return PlacedBuildingActors; }
	UCarnivalBuildComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build")
	bool bIsBuildModeActive;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build|Settings")
	float GridSnapSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build|Settings")
	float MaxBuildDistance;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build|Settings")
	UMaterialInterface* HologramMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Build|Categories")
	TArray<FCarnivalBuildCategory> Categories;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	int32 CurrentCategoryIndex;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	int32 CurrentPieceIndex;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	float CurrentYawRotation;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	FTransform CurrentHologramTransform;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	bool bCanPlacePiece = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Build|State")
	FString PlacementFeedback;

	/* API */
	UFUNCTION(BlueprintCallable, Category = "Build")
	void ToggleBuildMode();

	UFUNCTION(BlueprintCallable, Category = "Build")
	void CyclePiece(int32 Step);

	UFUNCTION(BlueprintCallable, Category = "Build")
	void CycleCategory(int32 Step);

	UFUNCTION(BlueprintCallable, Category = "Build")
	void RotatePiece();

	UFUNCTION(BlueprintCallable, Category = "Build")
	bool PlacePiece();

	UFUNCTION(BlueprintCallable, Category = "Build")
	bool DemolishPiece();

	UFUNCTION(BlueprintCallable, Category = "Build")
	UStaticMesh* GetCurrentPieceMesh() const;

	UFUNCTION(BlueprintCallable, Category = "Build")
	FString GetCurrentCategoryName() const;

protected:
	virtual void BeginPlay() override;

	void UpdateHologram();

	UPROPERTY()
	UStaticMeshComponent* HologramComponent;

	UPROPERTY()
	TArray<AActor*> PlacedBuildingActors;
};
