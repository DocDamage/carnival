#include "CarnivalVehicleAuthoring.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkeletalMeshSocket.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#if WITH_EDITOR
#include "Kismet2/BlueprintEditorUtils.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "Animation/InputScaleBias.h"
#include "UObject/UnrealType.h"
#endif

UPhysicsAsset* UCarnivalVehicleAuthoring::CreateBodyCollision(USkeletalMesh* Mesh, const FString& PackagePath,
    float LowerHalfWidth, float SplitHeight)
{
#if WITH_EDITOR
    // Author only local Carnival assets. An existing asset must already target
    // this mesh and contain exactly the single body this tool authors.
    if (!Mesh || Mesh->GetRefSkeleton().GetNum() != 1
        || !Mesh->GetPathName().StartsWith(TEXT("/Game/Carnival/"))
        || !PackagePath.StartsWith(TEXT("/Game/Carnival/"))
        || !FPackageName::IsValidLongPackageName(PackagePath)) return nullptr;
    UPhysicsAsset* Asset = nullptr;
    if (FPackageName::DoesPackageExist(PackagePath))
    {
        Asset = LoadObject<UPhysicsAsset>(nullptr, *PackagePath);
        if (!Asset || Asset->GetPreviewMesh() != Mesh || Asset->SkeletalBodySetups.Num() != 1) return nullptr;
    }
    else
    {
        UPackage* Package = CreatePackage(*PackagePath);
        Asset = NewObject<UPhysicsAsset>(Package,
            *FPackageName::GetLongPackageAssetName(PackagePath), RF_Public | RF_Standalone | RF_Transactional);
    }
    USkeletalBodySetup* Body = Asset->SkeletalBodySetups.IsEmpty()
        ? NewObject<USkeletalBodySetup>(Asset, NAME_None, RF_Transactional) : Asset->SkeletalBodySetups[0].Get();
    Body->BoneName = Mesh->GetRefSkeleton().GetBoneName(0);
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    const FTransform Bone = Mesh->GetRefSkeleton().GetRefBonePose()[0];
    const FVector Scale = Bone.GetScale3D().GetAbs();
    Body->AggGeom.EmptyElements();
    auto AddBox = [&](FVector Center, FVector Extent)
    {
        FKBoxElem Box;
        Box.Center = Bone.InverseTransformPosition(Center);
        Box.Rotation = Bone.GetRotation().Inverse().Rotator();
        Box.X = Extent.X * 2.f / FMath::Max(Scale.X, .001);
        Box.Y = Extent.Y * 2.f / FMath::Max(Scale.Y, .001);
        Box.Z = Extent.Z * 2.f / FMath::Max(Scale.Z, .001);
        Body->AggGeom.BoxElems.Add(Box);
    };
    const float Bottom = Bounds.Origin.Z - Bounds.BoxExtent.Z;
    const float Top = Bounds.Origin.Z + Bounds.BoxExtent.Z;
    if (LowerHalfWidth > 0.f && SplitHeight > Bottom && SplitHeight < Top)
    {
        AddBox(FVector(Bounds.Origin.X, Bounds.Origin.Y, (Bottom + SplitHeight) * .5f),
            FVector(Bounds.BoxExtent.X, FMath::Min(double(LowerHalfWidth), Bounds.BoxExtent.Y), (SplitHeight - Bottom) * .5f));
        AddBox(FVector(Bounds.Origin.X, Bounds.Origin.Y, (Top + SplitHeight) * .5f),
            FVector(Bounds.BoxExtent.X, Bounds.BoxExtent.Y, (Top - SplitHeight) * .5f));
    }
    else AddBox(Bounds.Origin, Bounds.BoxExtent);
    Body->CollisionTraceFlag = CTF_UseSimpleAsComplex;
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

USkeletalMeshSocket* UCarnivalVehicleAuthoring::SetAttachmentSocket(USkeletalMesh* Mesh,
    FName SocketName, FName BoneName, FVector Location)
{
#if WITH_EDITOR
    if (!Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/Carnival/"))
        || SocketName.IsNone() || Mesh->GetRefSkeleton().FindBoneIndex(BoneName) == INDEX_NONE) return nullptr;
    USkeletalMeshSocket* Socket = Mesh->FindSocket(SocketName);
    if (Socket && Socket->GetOuter() != Mesh) return nullptr;
    if (!Socket)
    {
        Socket = NewObject<USkeletalMeshSocket>(Mesh, NAME_None, RF_Transactional);
        Socket->SocketName = SocketName;
        Mesh->AddSocket(Socket);
    }
    Socket->BoneName = BoneName;
    Socket->RelativeLocation = Location;
    Socket->RelativeRotation = FRotator::ZeroRotator;
    Socket->RelativeScale = FVector::OneVector;
    Mesh->MarkPackageDirty();
    return Socket;
#else
    return nullptr;
#endif
}

int32 UCarnivalVehicleAuthoring::ConfigureMountedFootRig(UBlueprint* Blueprint)
{
#if WITH_EDITOR
    if (!Blueprint || !Blueprint->GetPathName().StartsWith(TEXT("/Game/Carnival/"))) return 0;
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    int32 Changed = 0;
    for (UEdGraph* Graph : Graphs) for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node || Node->GetClass()->GetFName() != TEXT("AnimGraphNode_ControlRig")) continue;
        // Control Rig exposes these editor properties but keeps the C++ members
        // private. Use their reflected types, with validation before mutation.
        auto* Struct = FindFProperty<FStructProperty>(Node->GetClass(), TEXT("Node"));
        if (!Struct) continue;
        auto* Type = FindFProperty<FEnumProperty>(Struct->Struct, TEXT("AlphaInputType"));
        auto* Curve = FindFProperty<FNameProperty>(Struct->Struct, TEXT("AlphaCurveName"));
        auto* Clamp = FindFProperty<FStructProperty>(Struct->Struct, TEXT("AlphaScaleBiasClamp"));
        if (!Type || !Curve || !Clamp || Clamp->Struct != FInputScaleBiasClamp::StaticStruct()) continue;
        const int64 CurveValue = Type->GetEnum()->GetValueByNameString(TEXT("Curve"));
        if (CurveValue == INDEX_NONE) continue;
        Node->Modify();
        void* Data = Struct->ContainerPtrToValuePtr<void>(Node);
        Type->GetUnderlyingProperty()->SetIntPropertyValue(Type->ContainerPtrToValuePtr<void>(Data), CurveValue);
        Curve->SetPropertyValue_InContainer(Data, TEXT("DisableLegIK"));
        FInputScaleBiasClamp& Settings = *Clamp->ContainerPtrToValuePtr<FInputScaleBiasClamp>(Data);
        Settings = FInputScaleBiasClamp();
        Settings.Scale = -1.f;
        Settings.Bias = 1.f;
        Node->ReconstructNode();
        // The exposed curve pin's literal is compiled over the struct default.
        if (UEdGraphPin* Pin = Node->FindPin(TEXT("AlphaCurveName")))
        {
            Pin->BreakAllPinLinks();
            Pin->DefaultValue = TEXT("DisableLegIK");
        }
        ++Changed;
    }
    if (Changed) FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    return Changed;
#else
    return 0;
#endif
}
