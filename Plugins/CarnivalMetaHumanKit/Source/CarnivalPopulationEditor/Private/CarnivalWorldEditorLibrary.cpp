#include "CarnivalWorldEditorLibrary.h"
#include "Landscape.h"
#include "LandscapeProxy.h"
#include "LandscapeInfo.h"
#include "LandscapeEdit.h"
#include "LandscapeEditLayer.h"
#include "LandscapeDataAccess.h"
#include "Components/SplineComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "InstancedFoliageActor.h"
#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "EdGraph/EdGraph.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Components/BoxComponent.h"
#include "Components/PostProcessComponent.h"

AActor* UCarnivalWorldEditorLibrary::CreateWetlandsPostProcess(UWorld* World, FVector Center, FVector Extent)
{
    if (!World) return nullptr;
    AActor* Actor = World->SpawnActor<AActor>();
    Actor->SetActorLabel(TEXT("Wetlands_ViewClarity"));
    UBoxComponent* Bounds = NewObject<UBoxComponent>(Actor, TEXT("Bounds"), RF_Transactional);
    Actor->AddInstanceComponent(Bounds);
    Actor->SetRootComponent(Bounds);
    Bounds->SetBoxExtent(Extent);
    Bounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Bounds->RegisterComponent();
    Actor->SetActorLocation(Center);
    UPostProcessComponent* Process = NewObject<UPostProcessComponent>(Actor, TEXT("PostProcess"), RF_Transactional);
    Actor->AddInstanceComponent(Process);
    Process->SetupAttachment(Bounds);
    Process->bUnbound = false;
    Process->Priority = 50.0f;
    Process->BlendRadius = 1500.0f;
    Process->Settings.bOverride_LensFlareIntensity = true;
    Process->Settings.LensFlareIntensity = 0.0f;
    Process->Settings.bOverride_BloomIntensity = true;
    Process->Settings.BloomIntensity = 0.2f;
    Process->Settings.bOverride_SceneFringeIntensity = true;
    Process->Settings.SceneFringeIntensity = 0.0f;
    Process->RegisterComponent();
    Actor->MarkPackageDirty();
    return Actor;
}

int32 UCarnivalWorldEditorLibrary::ClearConnectedLevelDemoEvents(UWorld* World)
{
    if (!World || !World->GetOutermost()->GetName().StartsWith(TEXT("/Game/Carnival/World/Levels/"))) return 0;
    ULevelScriptBlueprint* Blueprint = World->PersistentLevel->GetLevelScriptBlueprint(true);
    if (!Blueprint) return 0;
    Blueprint->Modify();
    int32 Removed = 0;
    for (UEdGraph* Graph : Blueprint->UbergraphPages)
    {
        Graph->Modify();
        const auto Nodes = Graph->Nodes;
        for (UEdGraphNode* Node : Nodes)
        {
            FBlueprintEditorUtils::RemoveNode(Blueprint, Node, true);
            ++Removed;
        }
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
    World->MarkPackageDirty();
    return Removed;
}

TArray<float> UCarnivalWorldEditorLibrary::SampleLandscapeHeights(AActor* Actor, const TArray<FVector>& Positions)
{
    TArray<float> Heights;
    ALandscapeProxy* Landscape = Cast<ALandscapeProxy>(Actor);
    if (!Landscape) return Heights;
    Heights.Reserve(Positions.Num());
    for (const FVector& Position : Positions)
    {
        const TOptional<float> Height = Landscape->GetHeightAtLocation(Position);
        Heights.Add(Height.Get(0.0f));
    }
    return Heights;
}

bool UCarnivalWorldEditorLibrary::StampLandscapeHeightGrid(AActor* Actor, const FTransform& GridToWorld,
    int32 SizeX, int32 SizeY, float Spacing, const TArray<float>& Heights, float EdgeFalloff)
{
    ALandscapeProxy* Proxy = Cast<ALandscapeProxy>(Actor);
    ALandscape* Landscape = Proxy ? Proxy->GetLandscapeActor() : nullptr;
    ULandscapeInfo* Info = Landscape ? Landscape->GetLandscapeInfo() : nullptr;
    if (!Info || Landscape->GetWorld()->IsGameWorld() || SizeX < 2 || SizeY < 2 || Spacing <= 0 || Heights.Num() != SizeX*SizeY) return false;
    const ULandscapeEditLayerBase* Layer = Landscape->GetEditLayer(0);
    if (!Layer) return false;

    const FTransform LandscapeToWorld = Proxy->LandscapeActorToWorld();
    const double Width = (SizeX-1)*Spacing, Depth = (SizeY-1)*Spacing;
    FBox LocalBox(ForceInit);
    for (double X : {0.0, Width}) for (double Y : {0.0, Depth})
        LocalBox += LandscapeToWorld.InverseTransformPosition(GridToWorld.TransformPosition(FVector(X,Y,0)));
    int32 MinX,MinY,MaxX,MaxY;
    if (!Info->GetLandscapeExtent(MinX,MinY,MaxX,MaxY)) return false;
    MinX=FMath::Max(MinX,FMath::FloorToInt(LocalBox.Min.X));
    MinY=FMath::Max(MinY,FMath::FloorToInt(LocalBox.Min.Y));
    MaxX=FMath::Min(MaxX,FMath::CeilToInt(LocalBox.Max.X));
    MaxY=FMath::Min(MaxY,FMath::CeilToInt(LocalBox.Max.Y));
    if (MaxX<MinX || MaxY<MinY) return false;
    Landscape->Modify();
    FHeightmapAccessor<false> Accessor(Info);
    Accessor.SetEditLayer(Layer->GetGuid());
    TArray<uint16> Data;
    const int32 RowWidth=MaxX-MinX+1;
    Data.SetNumUninitialized(RowWidth*(MaxY-MinY+1));
    Accessor.GetDataFast(MinX,MinY,MaxX,MaxY,Data.GetData());
    for (int32 Y=MinY;Y<=MaxY;++Y) for (int32 X=MinX;X<=MaxX;++X)
    {
        uint16& Value=Data[(Y-MinY)*RowWidth+X-MinX];
        const FVector World=LandscapeToWorld.TransformPosition(FVector(X,Y,LandscapeDataAccess::GetLocalHeight(Value)));
        const FVector Grid=GridToWorld.InverseTransformPosition(World);
        if (Grid.X<0 || Grid.Y<0 || Grid.X>Width || Grid.Y>Depth) continue;
        const int32 GX=FMath::Min(FMath::FloorToInt(Grid.X/Spacing),SizeX-2);
        const int32 GY=FMath::Min(FMath::FloorToInt(Grid.Y/Spacing),SizeY-2);
        const float TX=Grid.X/Spacing-GX, TY=Grid.Y/Spacing-GY;
        const float Z=FMath::Lerp(FMath::Lerp(Heights[GY*SizeX+GX],Heights[GY*SizeX+GX+1],TX),
            FMath::Lerp(Heights[(GY+1)*SizeX+GX],Heights[(GY+1)*SizeX+GX+1],TX),TY);
        const double Edge=FMath::Min(FMath::Min(Grid.X,Width-Grid.X),FMath::Min(Grid.Y,Depth-Grid.Y));
        float Alpha=EdgeFalloff>0 ? FMath::Clamp(Edge/EdgeFalloff,0.0,1.0) : 1.0;
        Alpha=Alpha*Alpha*(3.0f-2.0f*Alpha);
        const FVector Target=GridToWorld.TransformPosition(FVector(Grid.X,Grid.Y,Z));
        // Other edit layers may already contribute terrain height. Change this
        // layer by the required delta instead of adding a second absolute height.
        const float MergedZ=Proxy->GetHeightAtLocation(World).Get(World.Z);
        const float LocalZ=LandscapeToWorld.InverseTransformPosition(FVector(World.X,World.Y,World.Z+(Target.Z-MergedZ)*Alpha)).Z;
        Value=LandscapeDataAccess::GetTexHeight(LocalZ);
    }
    Accessor.SetData(MinX,MinY,MaxX,MaxY,Data.GetData());
    Accessor.Flush();
    Landscape->RequestLayersContentUpdateForceAll(ELandscapeLayerUpdateMode::Update_All,true);
    Landscape->MarkPackageDirty();
    return true;
}

bool UCarnivalWorldEditorLibrary::GradeLandscapeRoute(AActor* Actor,const TArray<FVector>& Points,float HalfWidth,float SideFalloff)
{
    ALandscapeProxy* Proxy=Cast<ALandscapeProxy>(Actor);
    ALandscape* Landscape=Proxy ? Proxy->GetLandscapeActor() : nullptr;
    if (!Landscape || Landscape->GetWorld()->IsGameWorld() || Points.Num()<2 || HalfWidth<=0) return false;
    const ULandscapeEditLayerBase* Layer=Landscape->GetEditLayer(0);
    if (!Layer) return false;
    ULandscapeInfo* Info=Landscape->GetLandscapeInfo();
    const FTransform LandscapeToWorld=Proxy->LandscapeActorToWorld();
    FBox Bounds(ForceInit);
    for (const FVector& P:Points) Bounds+=P;
    Bounds=Bounds.ExpandBy(HalfWidth+SideFalloff);
    FBox LocalBox=Bounds.TransformBy(LandscapeToWorld.ToInverseMatrixWithScale());
    int32 MinX,MinY,MaxX,MaxY;
    if (!Info->GetLandscapeExtent(MinX,MinY,MaxX,MaxY)) return false;
    MinX=FMath::Max(MinX,FMath::FloorToInt(LocalBox.Min.X));MinY=FMath::Max(MinY,FMath::FloorToInt(LocalBox.Min.Y));
    MaxX=FMath::Min(MaxX,FMath::CeilToInt(LocalBox.Max.X));MaxY=FMath::Min(MaxY,FMath::CeilToInt(LocalBox.Max.Y));
    if (MaxX<MinX || MaxY<MinY) return false;
    Landscape->Modify();
    FHeightmapAccessor<false> Accessor(Info);Accessor.SetEditLayer(Layer->GetGuid());
    const int32 RowWidth=MaxX-MinX+1;
    TArray<uint16> Data;Data.SetNumUninitialized(RowWidth*(MaxY-MinY+1));
    Accessor.GetDataFast(MinX,MinY,MaxX,MaxY,Data.GetData());
    for (int32 Y=MinY;Y<=MaxY;++Y) for (int32 X=MinX;X<=MaxX;++X)
    {
        uint16& Value=Data[(Y-MinY)*RowWidth+X-MinX];
        const FVector World=LandscapeToWorld.TransformPosition(FVector(X,Y,LandscapeDataAccess::GetLocalHeight(Value)));
        const FVector2D XY(World.X,World.Y);
        double Closest=DBL_MAX,TargetZ=World.Z;
        for (int32 I=0;I<Points.Num()-1;++I)
        {
            const FVector2D A(Points[I].X,Points[I].Y),B(Points[I+1].X,Points[I+1].Y),D=B-A;
            const double T=FMath::Clamp(FVector2D::DotProduct(XY-A,D)/FMath::Max(D.SizeSquared(),1.0),0.0,1.0);
            const double Dist=(XY-(A+D*T)).SizeSquared();
            if (Dist<Closest) {Closest=Dist;TargetZ=FMath::Lerp(Points[I].Z,Points[I+1].Z,T);}
        }
        const double Dist=FMath::Sqrt(Closest);
        if (Dist>HalfWidth+SideFalloff) continue;
        double Alpha=Dist<=HalfWidth ? 1.0 : FMath::Clamp(1.0-(Dist-HalfWidth)/FMath::Max(SideFalloff,1.0f),0.0,1.0);
        Alpha=Alpha*Alpha*(3.0-2.0*Alpha);
        const float MergedZ=Proxy->GetHeightAtLocation(World).Get(World.Z);
        const FVector Changed(World.X,World.Y,World.Z+(TargetZ-MergedZ)*Alpha);
        Value=LandscapeDataAccess::GetTexHeight(LandscapeToWorld.InverseTransformPosition(Changed).Z);
    }
    Accessor.SetData(MinX,MinY,MaxX,MaxY,Data.GetData());Accessor.Flush();
    Landscape->RequestLayersContentUpdateForceAll(ELandscapeLayerUpdateMode::Update_All,true);
    Landscape->MarkPackageDirty();
    return true;
}

AActor* UCarnivalWorldEditorLibrary::CreateMeshInstances(UWorld* World,UStaticMesh* Mesh,
    const TArray<FTransform>& Transforms,const FString& Label,bool EnableCollision)
{
    if (!World || World->IsGameWorld() || !Mesh || Transforms.IsEmpty()) return nullptr;
    AActor* Actor=World->SpawnActor<AActor>();
    Actor->SetActorLabel(Label);
    UHierarchicalInstancedStaticMeshComponent* Component=NewObject<UHierarchicalInstancedStaticMeshComponent>(Actor,TEXT("Instances"),RF_Transactional);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetStaticMesh(Mesh);
    Component->SetCollisionProfileName(EnableCollision ? TEXT("BlockAll") : TEXT("NoCollision"));
    Component->SetCullDistances(EnableCollision ? 60000 : 16000, EnableCollision ? 90000 : 24000);
    Actor->SetRootComponent(Component);
    Actor->AddInstanceComponent(Component);
    Component->RegisterComponent();
    Component->AddInstances(Transforms,false,true);
    Actor->MarkPackageDirty();
    return Actor;
}

int32 UCarnivalWorldEditorLibrary::ClearFoliageFromRoute(AActor* Actor,const TArray<FVector>& Points,float Radius)
{
    AInstancedFoliageActor* Foliage=Cast<AInstancedFoliageActor>(Actor);
    if (!Foliage || Foliage->GetWorld()->IsGameWorld() || Points.Num()<2 || Radius<=0) return 0;
    Foliage->Modify();
    int32 Count=0;
    FBox2D Bounds(ForceInit);
    for (const FVector& P:Points) Bounds+=FVector2D(P.X,P.Y);
    Bounds=Bounds.ExpandBy(Radius);
    Foliage->ForEachFoliageInfo([&](UFoliageType*,FFoliageInfo& Info)
    {
        TArray<int32> Remove;
        for (int32 I=0;I<Info.Instances.Num();++I)
        {
            const FVector L=Info.Instances[I].Location;
            const FVector2D P(L.X,L.Y);
            if (!Bounds.IsInside(P)) continue;
            for (int32 J=0;J<Points.Num()-1;++J)
            {
                const FVector2D A(Points[J].X,Points[J].Y), B(Points[J+1].X,Points[J+1].Y), D=B-A;
                const double T=FMath::Clamp(FVector2D::DotProduct(P-A,D)/FMath::Max(D.SizeSquared(),1.0),0.0,1.0);
                if ((P-(A+D*T)).SizeSquared()<Radius*Radius) {Remove.Add(I);break;}
            }
        }
        Count+=Remove.Num();
        if (!Remove.IsEmpty()) Info.RemoveInstances(Remove,true);
        return true;
    });
    Foliage->MarkPackageDirty();
    return Count;
}
