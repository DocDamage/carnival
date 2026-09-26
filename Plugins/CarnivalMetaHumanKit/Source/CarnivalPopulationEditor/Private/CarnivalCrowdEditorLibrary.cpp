#include "CarnivalCrowdEditorLibrary.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Animation/AnimSequence.h"
#include "Editor.h"
#include "Engine/World.h"
#include "MassCrowdMemberTrait.h"
#include "MassEntityConfigAsset.h"
#include "MassEntitySpawnDataGeneratorBase.h"
#include "MassEntityZoneGraphSpawnPointsGenerator.h"
#include "MassSpawner.h"
#include "MassSpawnerTypes.h"
#include "MassVisualizationTrait.h"
#include "Mass/MetaHumanMassCrowdVisualizationTrait.h"
#include "MetaHumanCrowdAnimationConfig.h"
#include "MetaHumanCharacter.h"
#include "MetaHumanCharacterPaletteItem.h"
#include "MetaHumanCollection.h"
#include "MetaHumanCrowdEditorPipeline.h"
#include "Item/MetaHumanCrowdGroomEditorPipeline.h"
#include "Item/MetaHumanCrowdGroomPipeline.h"
#include "MetaHumanCrowdPipeline.h"
#include "Item/MetaHumanCrowdCharacterEditorPipeline.h"
#include "MetaHumanInstance.h"
#include "MetaHumanItemPipeline.h"
#include "MetaHumanPaletteItemKey.h"
#include "MetaHumanPipelineSlotSelection.h"
#include "MetaHumanWardrobeItem.h"
#include "ZoneGraphData.h"
#include "ZoneGraphDelegates.h"
#include "ZoneGraphSettings.h"
#include "ZoneGraphSubsystem.h"
#include "ZoneShapeActor.h"
#include "ZoneShapeComponent.h"
#include "UObject/Package.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UnrealType.h"
#include "EngineUtils.h"
#include "HAL/PlatformApplicationMisc.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"

namespace CarnivalCrowdEditorPrivate
{
    template<typename T>
    T* FindOrCreateAsset(const FString& ObjectPath, FString& OutError)
    {
        if (!FPackageName::IsValidLongPackageName(ObjectPath))
        {
            OutError = FString::Printf(TEXT("Invalid package path: %s"), *ObjectPath);
            return nullptr;
        }

        const FString AssetName = FPaths::GetCleanFilename(ObjectPath);
        if (AssetName.IsEmpty())
        {
            OutError = FString::Printf(TEXT("No asset name in package path: %s"), *ObjectPath);
            return nullptr;
        }

        if (UObject* Existing = StaticLoadObject(T::StaticClass(), nullptr, *FString::Printf(TEXT("%s.%s"), *ObjectPath, *AssetName)))
        {
            if (T* TypedExisting = Cast<T>(Existing))
            {
                return TypedExisting;
            }
            OutError = FString::Printf(TEXT("An asset already exists at %s with class %s"), *ObjectPath, *Existing->GetClass()->GetName());
            return nullptr;
        }

        UPackage* Package = CreatePackage(*ObjectPath);
        if (!Package)
        {
            OutError = FString::Printf(TEXT("Could not create package %s"), *ObjectPath);
            return nullptr;
        }

        T* Asset = NewObject<T>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (!Asset)
        {
            OutError = FString::Printf(TEXT("Could not create asset %s"), *ObjectPath);
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Asset);
        Package->MarkPackageDirty();
        return Asset;
    }

    bool IsCharacterAlreadyInSlot(const UMetaHumanCollection* Collection, const UMetaHumanCharacter* Character, const FName SlotName)
    {
        for (const FMetaHumanCharacterPaletteItem& Item : Collection->GetItems())
        {
            if (Item.SlotName == SlotName && Item.LoadPrincipalAssetSynchronous() == Character)
            {
                return true;
            }
        }
        return false;
    }

    void AddSkeletonIfNeeded(USkeleton* TargetSkeleton, USkeletalMesh* Mesh)
    {
        if (TargetSkeleton && Mesh)
        {
            if (USkeleton* SourceSkeleton = Mesh->GetSkeleton(); SourceSkeleton && SourceSkeleton != TargetSkeleton)
            {
                TargetSkeleton->AddCompatibleSkeleton(SourceSkeleton);
            }
        }
    }

    void AddSkeletonIfNeeded(USkeleton* TargetSkeleton, USkeleton* SourceSkeleton)
    {
        if (TargetSkeleton && SourceSkeleton && SourceSkeleton != TargetSkeleton)
        {
            TargetSkeleton->AddCompatibleSkeleton(SourceSkeleton);
        }
    }

    FZoneLaneProfile* FindOrCreateCarnivalPedestrianProfile(UZoneGraphSettings* Settings, const float LaneWidth, FString& OutError)
    {
        FArrayProperty* ProfilesProperty = FindFProperty<FArrayProperty>(Settings->GetClass(), TEXT("LaneProfiles"));
        if (!ProfilesProperty)
        {
            OutError = TEXT("UE 5.8 ZoneGraphSettings has no LaneProfiles property.");
            return nullptr;
        }

        TArray<FZoneLaneProfile>* Profiles = ProfilesProperty->ContainerPtrToValuePtr<TArray<FZoneLaneProfile>>(Settings);
        if (!Profiles)
        {
            OutError = TEXT("Could not access ZoneGraph lane profiles.");
            return nullptr;
        }

        const FName ProfileName(TEXT("Carnival_Pedestrian"));
        FZoneLaneProfile* Profile = Profiles->FindByPredicate([&ProfileName](const FZoneLaneProfile& Candidate)
        {
            return Candidate.Name == ProfileName;
        });

        if (!Profile)
        {
            FZoneLaneProfile NewProfile;
            NewProfile.Name = ProfileName;
            FZoneLaneDesc& Lane = NewProfile.Lanes.AddDefaulted_GetRef();
            Lane.Width = FMath::Max(50.0f, LaneWidth);
            Lane.Direction = EZoneLaneDirection::Forward;
            Lane.Tags = FZoneGraphTagMask(1);
            Profile = &Profiles->Add_GetRef(MoveTemp(NewProfile));
            Settings->SaveConfig();
        }

        return Profile;
    }

    AZoneShape* FindShapeByName(UWorld* World, const FName Name)
    {
        for (TActorIterator<AZoneShape> It(World); It; ++It)
        {
            if (It->GetFName() == Name)
            {
                return *It;
            }
        }
        return nullptr;
    }

    void SetIntProperty(UObject* Object, const FName Name, const int32 Value)
    {
        if (FIntProperty* Property = FindFProperty<FIntProperty>(Object->GetClass(), Name))
        {
            Property->SetPropertyValue_InContainer(Object, Value);
        }
    }

    void SetBoolProperty(UObject* Object, const FName Name, const bool Value)
    {
        if (FBoolProperty* Property = FindFProperty<FBoolProperty>(Object->GetClass(), Name))
        {
            Property->SetPropertyValue_InContainer(Object, Value);
        }
    }
}

UMetaHumanCollection* UCarnivalCrowdEditorLibrary::CreateCrowdCollectionForWardrobe(
    const FString& ObjectPath,
    USkeleton* TargetSkeleton,
    UMetaHumanCrowdAnimationConfig* AnimationConfig,
    FString& OutError)
{
    OutError.Reset();
    if (!TargetSkeleton)
    {
        OutError = TEXT("A project-owned crowd target skeleton is required.");
        return nullptr;
    }
    if (!AnimationConfig || AnimationConfig->AnimationsToBake.IsEmpty())
    {
        OutError = TEXT("A crowd animation config with at least one bake entry is required.");
        return nullptr;
    }

    UMetaHumanCollection* Collection = CarnivalCrowdEditorPrivate::FindOrCreateAsset<UMetaHumanCollection>(ObjectPath, OutError);
    if (!Collection)
    {
        return nullptr;
    }

    UClass* PipelineClass = StaticLoadClass(UMetaHumanCollectionPipeline::StaticClass(), nullptr, TEXT("/MetaHumanCrowd/BP_CrowdPipeline.BP_CrowdPipeline_C"));
    if (!PipelineClass)
    {
        OutError = TEXT("Could not load UE 5.8's /MetaHumanCrowd/BP_CrowdPipeline class.");
        return nullptr;
    }

    Collection->Modify();
    Collection->SetPipelineFromClass(PipelineClass);
    UMetaHumanCrowdPipeline* CrowdPipeline = Cast<UMetaHumanCrowdPipeline>(Collection->GetMutablePipeline());
    UMetaHumanCrowdEditorPipeline* EditorPipeline = CrowdPipeline ? Cast<UMetaHumanCrowdEditorPipeline>(CrowdPipeline->GetMutableEditorPipeline()) : nullptr;
    if (!EditorPipeline)
    {
        OutError = TEXT("The Crowd Pipeline asset did not create a MetaHumanCrowdEditorPipeline.");
        return nullptr;
    }

    EditorPipeline->TargetSkeleton = TargetSkeleton;
    EditorPipeline->AnimationConfig = AnimationConfig;
    TargetSkeleton->MarkPackageDirty();
    Collection->MarkPackageDirty();
    return Collection;
}

UMetaHumanCollection* UCarnivalCrowdEditorLibrary::CreateAndBuildCrowdCollection(
    const FString& ObjectPath,
    const TArray<UMetaHumanCharacter*>& Characters,
    USkeleton* TargetSkeleton,
    UMetaHumanCrowdAnimationConfig* AnimationConfig,
    FString& OutError)
{
    OutError.Reset();
    if (Characters.IsEmpty())
    {
        OutError = TEXT("At least one MetaHuman Character is required.");
        return nullptr;
    }
    if (!TargetSkeleton)
    {
        OutError = TEXT("A project-owned crowd target skeleton is required.");
        return nullptr;
    }
    if (!AnimationConfig || AnimationConfig->AnimationsToBake.IsEmpty())
    {
        OutError = TEXT("A crowd animation config with at least one bake entry is required.");
        return nullptr;
    }

    UMetaHumanCollection* Collection = CarnivalCrowdEditorPrivate::FindOrCreateAsset<UMetaHumanCollection>(ObjectPath, OutError);
    if (!Collection)
    {
        return nullptr;
    }

    UClass* PipelineClass = StaticLoadClass(UMetaHumanCollectionPipeline::StaticClass(), nullptr, TEXT("/MetaHumanCrowd/BP_CrowdPipeline.BP_CrowdPipeline_C"));
    if (!PipelineClass)
    {
        OutError = TEXT("Could not load UE 5.8's /MetaHumanCrowd/BP_CrowdPipeline class.");
        return nullptr;
    }

    Collection->Modify();
    Collection->SetPipelineFromClass(PipelineClass);
    UMetaHumanCrowdPipeline* CrowdPipeline = Cast<UMetaHumanCrowdPipeline>(Collection->GetMutablePipeline());
    UMetaHumanCrowdEditorPipeline* EditorPipeline = CrowdPipeline ? Cast<UMetaHumanCrowdEditorPipeline>(CrowdPipeline->GetMutableEditorPipeline()) : nullptr;
    if (!EditorPipeline)
    {
        OutError = TEXT("The Crowd Pipeline asset did not create a MetaHumanCrowdEditorPipeline.");
        return nullptr;
    }
    EditorPipeline->TargetSkeleton = TargetSkeleton;
    EditorPipeline->AnimationConfig = AnimationConfig;

    int32 AddedCharacterCount = 0;
    for (UMetaHumanCharacter* Character : Characters)
    {
        if (!Character)
        {
            continue;
        }

        if (!CarnivalCrowdEditorPrivate::IsCharacterAlreadyInSlot(Collection, Character, UMetaHumanCrowdPipeline::HeadSlotName))
        {
            FMetaHumanPaletteItemKey ItemKey;
            if (!Collection->TryAddItemFromPrincipalAsset(UMetaHumanCrowdPipeline::HeadSlotName, FSoftObjectPath(Character), ItemKey))
            {
                OutError = FString::Printf(TEXT("Could not add %s to the Crowd Head slot."), *Character->GetPathName());
                return nullptr;
            }
            ++AddedCharacterCount;
        }

        if (!CarnivalCrowdEditorPrivate::IsCharacterAlreadyInSlot(Collection, Character, UMetaHumanCrowdPipeline::BodySlotName))
        {
            FMetaHumanPaletteItemKey ItemKey;
            if (!Collection->TryAddItemFromPrincipalAsset(UMetaHumanCrowdPipeline::BodySlotName, FSoftObjectPath(Character), ItemKey))
            {
                OutError = FString::Printf(TEXT("Could not add %s to the Crowd Body slot."), *Character->GetPathName());
                return nullptr;
            }
            ++AddedCharacterCount;
        }
    }

    if (AddedCharacterCount == 0 && Collection->GetBuiltData().IsValid())
    {
        return Collection;
    }

    // The pipeline checks source mesh skeleton compatibility before generating its crowd meshes.
    // Add any already-assembled source skeletons up front so the 5.8 unattended build can proceed.
    for (const FMetaHumanCharacterPaletteItem& Item : Collection->GetItems())
    {
        const UMetaHumanItemPipeline* ItemPipeline = nullptr;
        static_cast<void>(Collection->TryResolveItemPipeline(FMetaHumanPaletteItemPath(Item.GetItemKey()), ItemPipeline));

        // UE 5.8 creates the native crowd groom editor pipeline without its stock
        // card materials. Assign the instanced crowd materials before building so
        // imported hair and facial-hair wardrobe items produce usable crowd data.
        if (const UMetaHumanCrowdGroomPipeline* GroomPipelineConst = Cast<UMetaHumanCrowdGroomPipeline>(ItemPipeline))
        {
            UMetaHumanCrowdGroomPipeline* GroomPipeline = const_cast<UMetaHumanCrowdGroomPipeline*>(GroomPipelineConst);
            if (UMetaHumanCrowdGroomEditorPipeline* GroomEditorPipeline =
                Cast<UMetaHumanCrowdGroomEditorPipeline>(GroomPipeline->GetMutableEditorPipeline()))
            {
                if (GroomEditorPipeline->CardsMaterial.IsNull())
                {
                    GroomEditorPipeline->CardsMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(
                        TEXT("/MetaHumanCrowd/Materials/MI_Hair_Cards_Instanced.MI_Hair_Cards_Instanced")));
                }
                if (GroomEditorPipeline->HelmetsMaterial.IsNull())
                {
                    GroomEditorPipeline->HelmetsMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(
                        TEXT("/MetaHumanCrowd/Materials/MI_Hair_Helmets_Instanced.MI_Hair_Helmets_Instanced")));
                }
                GroomEditorPipeline->MarkPackageDirty();
            }
        }

        const UMetaHumanCrowdCharacterEditorPipeline* CharacterPipeline = ItemPipeline
            ? Cast<UMetaHumanCrowdCharacterEditorPipeline>(ItemPipeline->GetEditorPipeline())
            : nullptr;
        if (CharacterPipeline)
        {
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, CharacterPipeline->FaceMesh);
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, CharacterPipeline->BodyMesh);
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, CharacterPipeline->MergedHeadAndBodyMesh);
        }
    }
    for (const FMetaHumanCrowdBakeAnimationData& Animation : AnimationConfig->AnimationsToBake)
    {
        if (Animation.BodyAnimSequence)
        {
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, Animation.BodyAnimSequence->GetSkeleton());
        }
        if (Animation.FaceAnimSequence)
        {
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, Animation.FaceAnimSequence->GetSkeleton());
        }
        if (Animation.MergedAnimSequence)
        {
            CarnivalCrowdEditorPrivate::AddSkeletonIfNeeded(TargetSkeleton, Animation.MergedAnimSequence->GetSkeleton());
        }
    }
    TargetSkeleton->MarkPackageDirty();

    EMetaHumanBuildStatus BuildStatus = EMetaHumanBuildStatus::Failed;
    Collection->Build(FInstancedStruct(), UMetaHumanCollection::FOnBuildComplete::CreateLambda(
        [&BuildStatus](const EMetaHumanBuildStatus Status)
        {
            BuildStatus = Status;
        }));

    if (BuildStatus != EMetaHumanBuildStatus::Succeeded)
    {
        OutError = TEXT("UE 5.8 failed to build the MetaHuman Crowd Collection. Review the editor log for the pipeline error.");
        return nullptr;
    }

    Collection->MarkPackageDirty();
    return Collection;
}

UMetaHumanCrowdAnimationConfig* UCarnivalCrowdEditorLibrary::CreateCrowdAnimationConfig(
    const FString& ObjectPath,
    UAnimSequence* IdleAnimation,
    UAnimSequence* WalkAnimation,
    FString& OutError)
{
    OutError.Reset();
    if (!IdleAnimation && !WalkAnimation)
    {
        OutError = TEXT("At least one idle or walk animation sequence is required.");
        return nullptr;
    }

    UMetaHumanCrowdAnimationConfig* Config = CarnivalCrowdEditorPrivate::FindOrCreateAsset<UMetaHumanCrowdAnimationConfig>(ObjectPath, OutError);
    if (!Config)
    {
        return nullptr;
    }

    Config->Modify();
    Config->FaceRootBoneName = FName(TEXT("head"));
    Config->AnimationsToBake.Reset();
    if (IdleAnimation)
    {
        FMetaHumanCrowdBakeAnimationData& IdleEntry = Config->AnimationsToBake.AddDefaulted_GetRef();
        IdleEntry.Name = FName(TEXT("Idle"));
        IdleEntry.BodyAnimSequence = IdleAnimation;
        IdleEntry.bLoop = true;
        IdleEntry.bRootMotion = false;
    }
    if (WalkAnimation)
    {
        FMetaHumanCrowdBakeAnimationData& WalkEntry = Config->AnimationsToBake.AddDefaulted_GetRef();
        WalkEntry.Name = FName(TEXT("Walk"));
        WalkEntry.BodyAnimSequence = WalkAnimation;
        WalkEntry.bLoop = true;
        WalkEntry.bRootMotion = false;
    }
    Config->MarkPackageDirty();
    return Config;
}

UMetaHumanInstance* UCarnivalCrowdEditorLibrary::CreateCrowdInstanceAsset(
    UMetaHumanCollection* Collection,
    UMetaHumanCharacter* Character,
    const FString& ObjectPath,
    FString& OutError)
{
    OutError.Reset();
    if (!Collection || !Character || !Collection->GetBuiltData().IsValid())
    {
        OutError = TEXT("A built Crowd Collection and a MetaHuman Character are required.");
        return nullptr;
    }

    UMetaHumanInstance* Instance = CarnivalCrowdEditorPrivate::FindOrCreateAsset<UMetaHumanInstance>(ObjectPath, OutError);
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetMetaHumanCollection(Collection);
    FMetaHumanPaletteItemKey HeadKey;
    FMetaHumanPaletteItemKey BodyKey;
    for (const FMetaHumanCharacterPaletteItem& Item : Collection->GetItems())
    {
        if (Item.LoadPrincipalAssetSynchronous() != Character)
        {
            continue;
        }
        if (Item.SlotName == UMetaHumanCrowdPipeline::HeadSlotName)
        {
            HeadKey = Item.GetItemKey();
        }
        else if (Item.SlotName == UMetaHumanCrowdPipeline::BodySlotName)
        {
            BodyKey = Item.GetItemKey();
        }
    }
    if (HeadKey.IsNull() || BodyKey.IsNull())
    {
        OutError = FString::Printf(TEXT("Collection is missing a Head or Body item for %s."), *Character->GetPathName());
        return nullptr;
    }

    if (!Instance->TryAddSlotSelection(FMetaHumanPipelineSlotSelection(UMetaHumanCrowdPipeline::HeadSlotName, HeadKey))
        || !Instance->TryAddSlotSelection(FMetaHumanPipelineSlotSelection(UMetaHumanCrowdPipeline::BodySlotName, BodyKey)))
    {
        OutError = FString::Printf(TEXT("Could not select %s for both Crowd slots."), *Character->GetPathName());
        return nullptr;
    }

    Instance->MarkPackageDirty();
    return Instance;
}

UMassEntityConfigAsset* UCarnivalCrowdEditorLibrary::CreateMetaHumanMassEntityConfig(
    const FString& ObjectPath,
    const TArray<UMetaHumanInstance*>& CharacterInstances,
    FString& OutError)
{
    OutError.Reset();
    if (CharacterInstances.IsEmpty())
    {
        OutError = TEXT("At least one built MetaHuman Instance is required for the Mass Entity Config.");
        return nullptr;
    }

    UMassEntityConfigAsset* Config = CarnivalCrowdEditorPrivate::FindOrCreateAsset<UMassEntityConfigAsset>(ObjectPath, OutError);
    if (!Config)
    {
        return nullptr;
    }

    UClass* CrowdActorClass = StaticLoadClass(AActor::StaticClass(), nullptr, TEXT("/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C"));
    if (!CrowdActorClass)
    {
        OutError = TEXT("Could not load UE 5.8's BP_CrowdActor class.");
        return nullptr;
    }

    Config->Modify();
    UMetaHumanMassCrowdVisualizationTrait* Visualization = Cast<UMetaHumanMassCrowdVisualizationTrait>(Config->AddTrait(UMetaHumanMassCrowdVisualizationTrait::StaticClass()));
    if (!Visualization)
    {
        OutError = TEXT("Could not add the MetaHuman Crowd Visualization trait to the Mass config.");
        return nullptr;
    }
    Visualization->CharacterInstances.Reset();
    for (UMetaHumanInstance* Instance : CharacterInstances)
    {
        if (Instance)
        {
            Visualization->CharacterInstances.Add(Instance);
        }
    }
    Visualization->HighResTemplateActor = CrowdActorClass;

    if (!Config->AddTrait(UMassCrowdMemberTrait::StaticClass()))
    {
        OutError = TEXT("Could not add the Mass CrowdMember trait to the Mass config.");
        return nullptr;
    }

    Config->MarkPackageDirty();
    return Config;
}

AActor* UCarnivalCrowdEditorLibrary::PlaceMetaHumanMassSpawner(
    UMassEntityConfigAsset* EntityConfig,
    const int32 Count,
    const FVector& Location,
    FString& OutError)
{
    OutError.Reset();
    if (!EntityConfig)
    {
        OutError = TEXT("A Mass Entity Config is required.");
        return nullptr;
    }
    if (!GEditor)
    {
        OutError = TEXT("The Unreal Editor is not available.");
        return nullptr;
    }

    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        OutError = TEXT("No editor world is loaded. Open LV_Carnival before placing the spawner.");
        return nullptr;
    }

    UClass* SpawnerClass = StaticLoadClass(AMassSpawner::StaticClass(), nullptr, TEXT("/Script/MetaHumanCrowd.MetaHumanMassSpawner"));
    if (!SpawnerClass)
    {
        OutError = TEXT("Could not load UE 5.8's MetaHumanMassSpawner class.");
        return nullptr;
    }

    const FName ActorName(TEXT("AMetaHumanCarnivalCrowdSpawner"));
    AActor* Spawner = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (It->GetFName() == ActorName)
        {
            Spawner = *It;
            break;
        }
    }
    if (!Spawner)
    {
        FActorSpawnParameters SpawnParameters;
        SpawnParameters.Name = ActorName;
        SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        Spawner = World->SpawnActor<AActor>(SpawnerClass, Location, FRotator::ZeroRotator, SpawnParameters);
    }
    if (!Spawner || !Spawner->IsA(SpawnerClass))
    {
        OutError = TEXT("Could not place a MetaHuman Mass Spawner in the level.");
        return nullptr;
    }

    Spawner->Modify();
    Spawner->SetActorLocation(Location);
    CarnivalCrowdEditorPrivate::SetIntProperty(Spawner, TEXT("Count"), FMath::Max(1, Count));
    CarnivalCrowdEditorPrivate::SetBoolProperty(Spawner, TEXT("bAutoSpawnOnBeginPlay"), true);

    FArrayProperty* EntityTypesProperty = FindFProperty<FArrayProperty>(SpawnerClass, TEXT("EntityTypes"));
    TArray<FMassSpawnedEntityType>* EntityTypes = EntityTypesProperty
        ? EntityTypesProperty->ContainerPtrToValuePtr<TArray<FMassSpawnedEntityType>>(Spawner)
        : nullptr;
    if (!EntityTypes)
    {
        OutError = TEXT("The MetaHuman Mass Spawner has no EntityTypes array.");
        return nullptr;
    }
    EntityTypes->Reset();
    FMassSpawnedEntityType& EntityType = EntityTypes->AddDefaulted_GetRef();
    EntityType.EntityConfig = EntityConfig;
    EntityType.Proportion = 1.0f;

    FArrayProperty* GeneratorsProperty = FindFProperty<FArrayProperty>(SpawnerClass, TEXT("SpawnDataGenerators"));
    TArray<FMassSpawnDataGenerator>* Generators = GeneratorsProperty
        ? GeneratorsProperty->ContainerPtrToValuePtr<TArray<FMassSpawnDataGenerator>>(Spawner)
        : nullptr;
    if (!Generators)
    {
        OutError = TEXT("The MetaHuman Mass Spawner has no SpawnDataGenerators array.");
        return nullptr;
    }
    Generators->Reset();
    FMassSpawnDataGenerator& Generator = Generators->AddDefaulted_GetRef();
    Generator.GeneratorClass = UMassEntityZoneGraphSpawnPointsGenerator::StaticClass();
    Generator.GeneratorInstance = NewObject<UMassEntityZoneGraphSpawnPointsGenerator>(Spawner, TEXT("CarnivalZoneGraphSpawnPointsGenerator"), RF_Transactional);
    Generator.Proportion = 1.0f;

    Spawner->MarkPackageDirty();
    return Spawner;
}

int32 UCarnivalCrowdEditorLibrary::CreateCrowdLoopZoneGraph(
    UWorld* World,
    const TArray<FVector>& Waypoints,
    const float LaneWidth,
    FString& OutError)
{
    OutError.Reset();
    if (!World || Waypoints.Num() < 3)
    {
        OutError = TEXT("A loaded level world and at least three loop waypoints are required.");
        return 0;
    }

    UZoneGraphSettings* Settings = GetMutableDefault<UZoneGraphSettings>();
    FZoneLaneProfile* LaneProfile = CarnivalCrowdEditorPrivate::FindOrCreateCarnivalPedestrianProfile(Settings, LaneWidth, OutError);
    if (!LaneProfile)
    {
        return 0;
    }
    const FZoneLaneProfileRef LaneProfileRef(*LaneProfile);

    int32 CreatedOrUpdated = 0;
    for (int32 Index = 0; Index < Waypoints.Num(); ++Index)
    {
        const int32 NextIndex = (Index + 1) % Waypoints.Num();
        if (FVector::DistSquared(Waypoints[Index], Waypoints[NextIndex]) < FMath::Square(200.0f))
        {
            OutError = FString::Printf(TEXT("ZoneGraph segment %d is too short; adjacent waypoints must be at least 200 cm apart."), Index);
            return 0;
        }

        const FName ShapeName(*FString::Printf(TEXT("ACarnivalCrowdLaneSegment_%02d"), Index));
        AZoneShape* Shape = CarnivalCrowdEditorPrivate::FindShapeByName(World, ShapeName);
        if (!Shape)
        {
            FActorSpawnParameters SpawnParameters;
            SpawnParameters.Name = ShapeName;
            SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            Shape = World->SpawnActor<AZoneShape>(AZoneShape::StaticClass(), FTransform::Identity, SpawnParameters);
        }
        if (!Shape)
        {
            OutError = FString::Printf(TEXT("Could not create ZoneGraph shape %s."), *ShapeName.ToString());
            return 0;
        }

        Shape->Modify();
        Shape->SetActorLabel(FString::Printf(TEXT("Carnival Crowd Lane %02d"), Index), true);
        UZoneShapeComponent* ShapeComponent = const_cast<UZoneShapeComponent*>(Shape->GetShape());
        if (!ShapeComponent)
        {
            OutError = FString::Printf(TEXT("ZoneGraph shape %s has no ZoneShapeComponent."), *ShapeName.ToString());
            return 0;
        }

        ShapeComponent->Modify();
        ShapeComponent->SetShapeType(FZoneShapeType::Spline);
        ShapeComponent->SetCommonLaneProfile(LaneProfileRef);
        TArray<FZoneShapePoint>& Points = ShapeComponent->GetMutablePoints();
        Points.Reset();
        Points.Add(FZoneShapePoint(Waypoints[Index]));
        Points.Add(FZoneShapePoint(Waypoints[NextIndex]));
        ShapeComponent->UpdateShape();
        ShapeComponent->MarkRenderStateDirty();
        Shape->MarkPackageDirty();
        ++CreatedOrUpdated;
    }

    // ZoneGraph owns its baked storage per level. This editor delegate creates missing storage
    // and rebuilds it from the lane shapes above.
    UE::ZoneGraphDelegates::OnZoneGraphRequestRebuild.Broadcast();
    return CreatedOrUpdated;
}

int32 UCarnivalCrowdEditorLibrary::CountBuiltZoneGraphLanes(UWorld* World)
{
    if (!World)
    {
        return 0;
    }

    int32 LaneCount = 0;
    if (const UZoneGraphSubsystem* Subsystem = World->GetSubsystem<UZoneGraphSubsystem>())
    {
        for (const FRegisteredZoneGraphData& RegisteredData : Subsystem->GetRegisteredZoneGraphData())
        {
            if (RegisteredData.bInUse && RegisteredData.ZoneGraphData)
            {
                LaneCount += RegisteredData.ZoneGraphData->GetStorage().Lanes.Num();
            }
        }
    }
    return LaneCount;
}
