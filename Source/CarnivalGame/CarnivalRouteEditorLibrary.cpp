#include "CarnivalRouteEditorLibrary.h"

#if WITH_EDITOR
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeEdit.h"
#include "LandscapeEditLayer.h"
#include "Engine/SkeletalMesh.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionLandscapeVisibilityMask.h"
#include "Materials/MaterialExpressionSetMaterialAttributes.h"
#endif

bool UCarnivalRouteEditorLibrary::CutLandscapeOpening(AActor* LandscapeActor, FVector WorldMinimum, FVector WorldMaximum, FTransform LevelTransform)
{
#if WITH_EDITOR
    ALandscape* Landscape = Cast<ALandscape>(LandscapeActor);
    if (!Landscape || !Landscape->GetOutermost()->GetName().StartsWith(TEXT("/Game/Carnival/World/Levels/"))) return false;
    ULandscapeInfo* Info = Landscape->GetLandscapeInfo();
    if (!Info || WorldMaximum.X <= WorldMinimum.X || WorldMaximum.Y <= WorldMinimum.Y ||
        WorldMaximum.X - WorldMinimum.X > 2000.0 || WorldMaximum.Y - WorldMinimum.Y > 8000.0) return false;
    // A copied actor must not paint weightmaps still owned by its source pack.
    for (ULandscapeComponent* Component : Landscape->LandscapeComponents)
    {
        if (!Component) continue;
        for (UTexture2D* Texture : Component->GetWeightmapTextures())
            if (Texture && Texture->GetOutermost() != Landscape->GetOutermost()) return false;
        for (const ULandscapeEditLayerBase* Layer : Landscape->GetEditLayersConst())
            if (Layer) for (UTexture2D* Texture : Component->GetWeightmapTextures(Layer->GetGuid()))
                if (Texture && Texture->GetOutermost() != Landscape->GetOutermost()) return false;
    }
    const FTransform Transform = Landscape->LandscapeActorToWorld() * LevelTransform;
    FBox LocalBounds(ForceInit);
    for (double X : {WorldMinimum.X, WorldMaximum.X})
        for (double Y : {WorldMinimum.Y, WorldMaximum.Y})
            LocalBounds += Transform.InverseTransformPosition(FVector(X,Y,Landscape->GetActorLocation().Z));
    int32 MinX, MinY, MaxX, MaxY;
    if (!Info->GetLandscapeExtent(MinX,MinY,MaxX,MaxY)) return false;
    const int32 X1=FMath::Max(MinX,FMath::FloorToInt(LocalBounds.Min.X)-1);
    const int32 Y1=FMath::Max(MinY,FMath::FloorToInt(LocalBounds.Min.Y)-1);
    const int32 X2=FMath::Min(MaxX,FMath::CeilToInt(LocalBounds.Max.X)+1);
    const int32 Y2=FMath::Min(MaxY,FMath::CeilToInt(LocalBounds.Max.Y)+1);
    if (X2<X1 || Y2<Y1 || int64(X2-X1+1)*(Y2-Y1+1)>1000000) return false;
    TAlphamapAccessor<false> Accessor(Info, ALandscapeProxy::VisibilityLayer);
    if (const ULandscapeEditLayerBase* Layer=Landscape->GetEditLayer(0)) Accessor.SetEditLayer(Layer->GetGuid());
    TArray<uint8> Data;
    Data.SetNumZeroed((X2-X1+1)*(Y2-Y1+1));
    Accessor.GetDataFast(X1,Y1,X2,Y2,Data.GetData());
    int32 Changed=0;
    for (int32 Y=Y1;Y<=Y2;++Y) for (int32 X=X1;X<=X2;++X)
    {
        const FVector World=Transform.TransformPosition(FVector(X,Y,0));
        if (World.X>=WorldMinimum.X && World.X<=WorldMaximum.X && World.Y>=WorldMinimum.Y && World.Y<=WorldMaximum.Y)
        { Data[(Y-Y1)*(X2-X1+1)+(X-X1)]=255; ++Changed; }
    }
    if (!Changed) return false;
    Landscape->Modify();
    Accessor.SetData(X1,Y1,X2,Y2,Data.GetData(),ELandscapeLayerPaintingRestriction::None);
    Accessor.Flush();
    Landscape->RequestLayersContentUpdateForceAll();
    Landscape->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

bool UCarnivalRouteEditorLibrary::AddLandscapeVisibilityMask(UMaterial* CopiedMaterial)
{
#if WITH_EDITOR
    if (!CopiedMaterial || !CopiedMaterial->GetPathName().StartsWith(TEXT("/Game/Carnival/World/Materials/")) || !CopiedMaterial->bUseMaterialAttributes) return false;
    UMaterialEditorOnlyData* Data=CopiedMaterial->GetEditorOnlyData();
    if (!Data || !Data->MaterialAttributes.Expression) return false;
    CopiedMaterial->Modify();
    auto* Mask=NewObject<UMaterialExpressionLandscapeVisibilityMask>(CopiedMaterial,NAME_None,RF_Transactional);
    auto* Attributes=NewObject<UMaterialExpressionSetMaterialAttributes>(CopiedMaterial,NAME_None,RF_Transactional);
    Mask->Material=CopiedMaterial;
    Attributes->Material=CopiedMaterial;
    *Attributes->GetInput(0)=Data->MaterialAttributes;
    if (!Attributes->ConnectInputAttribute(MP_OpacityMask,Mask)) return false;
    CopiedMaterial->GetExpressionCollection().AddExpression(Mask);
    CopiedMaterial->GetExpressionCollection().AddExpression(Attributes);
    Data->MaterialAttributes.Connect(0,Attributes);
    CopiedMaterial->BlendMode=BLEND_Masked;
    CopiedMaterial->PostEditChange();
    CopiedMaterial->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

UPhysicsAsset* UCarnivalRouteEditorLibrary::CreateSailAnchorCollision(USkeletalMesh* Mesh, const FString& PackagePath)
{
#if WITH_EDITOR
    if (!Mesh || Mesh->GetRefSkeleton().GetNum()!=1 || Mesh->GetRefSkeleton().GetBoneName(0)!=FName(TEXT("Sails_Torn")) ||
        !PackagePath.StartsWith(TEXT("/Game/Carnival/World/Physics/")) || !FPackageName::IsValidLongPackageName(PackagePath)) return nullptr;
    UPhysicsAsset* Asset=nullptr;
    if (FPackageName::DoesPackageExist(PackagePath))
    {
        Asset=LoadObject<UPhysicsAsset>(nullptr,*PackagePath);
        if (!Asset || Asset->GetPreviewMesh()!=Mesh || Asset->SkeletalBodySetups.Num()!=1) return nullptr;
    }
    else Asset=NewObject<UPhysicsAsset>(CreatePackage(*PackagePath),*FPackageName::GetLongPackageAssetName(PackagePath),RF_Public|RF_Standalone|RF_Transactional);
    USkeletalBodySetup* Body=Asset->SkeletalBodySetups.IsEmpty() ? NewObject<USkeletalBodySetup>(Asset,NAME_None,RF_Transactional) : Asset->SkeletalBodySetups[0].Get();
    Body->BoneName=Mesh->GetRefSkeleton().GetBoneName(0);
    Body->PhysicsType=PhysType_Kinematic;
    Body->AggGeom.EmptyElements();
    // Only the mast attachment has a rigid body. A full sail bounds box would
    // obstruct the authored passage through empty space between the cloths.
    FKSphereElem Anchor;
    Anchor.Center=FVector::ZeroVector;
    Anchor.Radius=10.f;
    Body->AggGeom.SphereElems.Add(Anchor);
    Body->CollisionTraceFlag=CTF_UseSimpleAsComplex;
    Body->InvalidatePhysicsData();
    Body->CreatePhysicsMeshes();
    if (Asset->SkeletalBodySetups.IsEmpty()) Asset->SkeletalBodySetups.Add(Body);
    Asset->UpdateBodySetupIndexMap();
    Asset->UpdateBoundsBodiesArray();
    Asset->SetPreviewMesh(Mesh);
    Asset->MarkPackageDirty();
    return Asset;
#else
    return nullptr;
#endif
}
