#include "CarnivalWaterVolume.h"
#include "Components/BoxComponent.h"
#include "Components/BrushComponent.h"
#include "EngineUtils.h"
#include "PhysicsEngine/BodySetup.h"

ACarnivalWaterVolume::ACarnivalWaterVolume(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bWaterVolume = true;
	FluidFriction = 0.3f;
	Priority = 10;
	UBrushComponent* BrushComp = GetBrushComponent();
	BrushComp->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	BrushComp->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);

	SurfaceLid = CreateDefaultSubobject<UBoxComponent>(TEXT("SurfaceLid"));
	SurfaceLid->SetupAttachment(BrushComp);
	SurfaceLid->SetCollisionProfileName(TEXT("NoCollision"));
	SurfaceLid->SetHiddenInGame(true);
}

float ACarnivalWaterVolume::GetSurfaceZ() const
{
	return GetActorTransform().TransformPosition(FVector(0.f, 0.f, WaterExtent.Z)).Z;
}

bool ACarnivalWaterVolume::ContainsPoint(const FVector& Point) const
{
	const FVector Local = GetActorTransform().InverseTransformPosition(Point);
	return FMath::Abs(Local.X) <= WaterExtent.X && FMath::Abs(Local.Y) <= WaterExtent.Y && FMath::Abs(Local.Z) <= WaterExtent.Z;
}

ACarnivalWaterVolume* ACarnivalWaterVolume::FindAt(const UWorld* World, const FVector& Point)
{
	ACarnivalWaterVolume* Best = nullptr;
	if (!World) return nullptr;
	for (TActorIterator<ACarnivalWaterVolume> It(const_cast<UWorld*>(World)); It; ++It)
	{
		if (It->ContainsPoint(Point) && (!Best || It->Priority > Best->Priority)) Best = *It;
	}
	return Best;
}

bool ACarnivalWaterVolume::IsOverlapInVolume(const USceneComponent& TestComponent) const
{
	return ContainsPoint(TestComponent.GetComponentLocation());
}

void ACarnivalWaterVolume::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	RebuildShape();
}

void ACarnivalWaterVolume::PostInitializeComponents()
{
	RebuildShape();
	Super::PostInitializeComponents();
}

void ACarnivalWaterVolume::RebuildShape()
{
	UBrushComponent* BrushComp = GetBrushComponent();
	if (!BrushComp) return;
	if (!BrushComp->BrushBodySetup || BrushComp->BrushBodySetup->GetOuter() != BrushComp)
	{
		BrushComp->BrushBodySetup = NewObject<UBodySetup>(BrushComp, TEXT("WaterBodySetup"), RF_Transactional);
	}
	UBodySetup* Body = BrushComp->BrushBodySetup;
	Body->AggGeom.EmptyElements();
	Body->AggGeom.BoxElems.Add(FKBoxElem(WaterExtent.X * 2.f, WaterExtent.Y * 2.f, WaterExtent.Z * 2.f));
	Body->CollisionTraceFlag = CTF_UseSimpleAsComplex;
	Body->InvalidatePhysicsData();
	Body->CreatePhysicsMeshes();
	if (BrushComp->IsRegistered())
	{
		BrushComp->RecreatePhysicsState();
		BrushComp->UpdateBounds();
		BrushComp->MarkRenderStateDirty();
	}

	// The lid sits just above the surface so a swimmer's head can reach the waterline but not leave it.
	SurfaceLid->SetBoxExtent(FVector(WaterExtent.X, WaterExtent.Y, 25.f));
	SurfaceLid->SetRelativeLocation(FVector(0.f, 0.f, WaterExtent.Z + 25.f));
	SurfaceLid->SetCollisionProfileName(bSolidSurface ? TEXT("BlockAllDynamic") : TEXT("NoCollision"));
	SurfaceLid->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	SurfaceLid->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
}
