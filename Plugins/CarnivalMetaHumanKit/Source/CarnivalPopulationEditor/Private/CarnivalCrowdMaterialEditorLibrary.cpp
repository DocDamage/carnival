#include "CarnivalCrowdMaterialEditorLibrary.h"

#include "MetaHumanCharacter.h"
#include "MetaHumanCharacterGeneratedAssets.h"
#include "MetaHumanCharacterEditorSubsystem.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInterface.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "TextureGraph.h"
#include "TG_Graph.h"
#include "TG_Material.h"
#include "Blueprint/TG_AsyncExportTask.h"
#include "UObject/StrongObjectPtr.h"
#include "RHI.h"
#include "Animation/Skeleton.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/SkeletonRemapping.h"
#include "Animation/SkeletonRemappingRegistry.h"
#include "Components/SkeletalMeshComponent.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "Misc/SecureHash.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "MetaHumanWardrobeItem.h"
#include "MetaHumanItemEditorPipeline.h"
#include "MetaHumanGeometryRemoval.h"
#include "UObject/UnrealType.h"
#include "SkinnedAssetCompiler.h"
#include "MetaHumanCollection.h"
#include "MetaHumanCollectionPipeline.h"
#include "MetaHumanCharacterPipelineSpecification.h"
#include "MetaHumanCharacterPaletteItem.h"
#include "MetaHumanCrowdEditorPipeline.h"
#include "MetaHumanCrowdAnimationConfig.h"
#include "MetaHumanCrowdPipeline.h"
#include "MetaHumanInstance.h"
#include "MetaHumanPipelineSlotSelection.h"
#include "MetaHumanPaletteItemKey.h"
#include "MetaHumanPinnedSlotSelection.h"
#include "Misc/PackageName.h"

FString UCarnivalCrowdMaterialEditorLibrary::DescribeMaterialExpressionInputs(UMaterialExpression* Expression)
{
    if (!Expression) return TEXT("{}");
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("expression"), Expression->GetPathName());
    TArray<TSharedPtr<FJsonValue>> Inputs;
    int32 Index = 0;
    for (FExpressionInputIterator It{Expression}; It; ++It, ++Index)
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("index"), Index);
        Row->SetStringField(TEXT("name"), Expression->GetInputName(Index).ToString());
        Row->SetStringField(TEXT("source"), It->Expression ? It->Expression->GetPathName() : FString());
        Row->SetNumberField(TEXT("output_index"), It->OutputIndex);
        Row->SetBoolField(TEXT("masked"), It->Mask != 0);
        Row->SetStringField(TEXT("channels"), FString(It->MaskR ? TEXT("R") : TEXT(""))
            + (It->MaskG ? TEXT("G") : TEXT("")) + (It->MaskB ? TEXT("B") : TEXT("")) + (It->MaskA ? TEXT("A") : TEXT("")));
        if (It->Expression)
        {
            const auto& Outputs = It->Expression->GetOutputs();
            Row->SetStringField(TEXT("output_name"), Outputs.IsValidIndex(It->OutputIndex) ? Outputs[It->OutputIndex].OutputName.ToString() : TEXT("Invalid"));
        }
        Inputs.Add(MakeShared<FJsonValueObject>(Row));
    }
    Result->SetArrayField(TEXT("inputs"), Inputs);
    FString Json; auto Writer = TJsonWriterFactory<>::Create(&Json); FJsonSerializer::Serialize(Result, Writer);
    return Json;
}

UMaterial* UCarnivalCrowdMaterialEditorLibrary::MakeCompactHairSamplerProof(UMaterialInterface* Current, FString& OutError)
{
    OutError.Reset();
    UMaterial* Source = Current ? Current->GetMaterial() : nullptr;
    if (!Current || !Current->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Source || Source->GetPathName() != TEXT("/MetaHumanCrowd/Materials/M_Hair_Instanced.M_Hair_Instanced"))
    { OutError = TEXT("Sampler proof requires an owned candidate using the inspected SDK hair master"); return nullptr; }
    TStrongObjectPtr<UMaterial> Proof(DuplicateObject<UMaterial>(Source, GetTransientPackage()));
    int32 Changed = 0;
    for (UMaterialExpression* Expression : Proof->GetExpressions())
    {
        auto* Sample = Cast<UMaterialExpressionTextureSampleParameter2D>(Expression);
        if (!Sample || (Sample->ParameterName != TEXT("Tangent-CoordU") && Sample->ParameterName != TEXT("Coverage-Depth-Seed"))) continue;
        UTexture* Texture = nullptr;
        if (!Current->GetTextureParameterValue(FMaterialParameterInfo(Sample->ParameterName), Texture)
            || !Texture || Texture->SRGB || Texture->CompressionSettings != TC_Masks || Sample->SamplerType != SAMPLERTYPE_Color)
        { OutError = TEXT("Hair atlas/sampler differs from the inspected linear mask inputs"); return nullptr; }
        Sample->Texture = Texture;
        Sample->SamplerType = SAMPLERTYPE_Masks;
        ++Changed;
    }
    if (Changed != 2) { OutError = TEXT("Expected exactly two compact hair atlas samplers"); return nullptr; }
    Proof->PostEditChange();
    return Proof.Get();
}

UAnimSequence* UCarnivalCrowdMaterialEditorLibrary::MakeAnimationRetargetPolicyProof(UAnimSequence* Baked,
    UAnimSequence* Reference, FString& OutError)
{
    OutError.Reset();
    if (!Baked || !Baked->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Baked->GetSkeleton() || !Reference || !Reference->GetSkeleton())
    {
        OutError = TEXT("Retargeting proof requires an owned candidate clip and a source skeleton.");
        return nullptr;
    }
    USkeleton* Skeleton = DuplicateObject<USkeleton>(Baked->GetSkeleton(), GetTransientPackage(), TEXT("SK_RetargetPolicyProof"));
    const USkeleton* Source = Reference->GetSkeleton();
    const FReferenceSkeleton& TargetRef = Skeleton->GetReferenceSkeleton();
    const FReferenceSkeleton& SourceRef = Source->GetReferenceSkeleton();
    int32 Matched = 0;
    for (int32 I = 0; I < TargetRef.GetNum(); ++I)
    {
        const int32 SourceIndex = SourceRef.FindBoneIndex(TargetRef.GetBoneName(I));
        if (SourceIndex == INDEX_NONE) continue;
        Skeleton->SetBoneTranslationRetargetingMode(I, Source->GetBoneTranslationRetargetingMode(SourceIndex), false);
        ++Matched;
    }
    if (Matched < 50)
    {
        OutError = TEXT("Too few matching body bones for a scoped translation-policy proof.");
        return nullptr;
    }
    Skeleton->AddCompatibleSkeleton(Baked->GetSkeleton());
    UAnimSequence* Proof = DuplicateObject<UAnimSequence>(Baked, GetTransientPackage(), TEXT("AS_RetargetPolicyProof"));
    Proof->SetSkeleton(Skeleton);
    Proof->PostEditChange();
    return Proof;
}

UAnimSequence* UCarnivalCrowdMaterialEditorLibrary::MakeAnimationRetargetReferenceProof(UAnimSequence* Baked,
    UAnimSequence* Reference, bool CopyTranslationModes, FString& OutError)
{
    OutError.Reset();
    if (!Baked || !Baked->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Baked->GetSkeleton() || !Reference || !Reference->GetSkeleton())
    {
        OutError = TEXT("Reference-pose proof requires an owned candidate clip and a source skeleton.");
        return nullptr;
    }
    const FName SkeletonName = MakeUniqueObjectName(GetTransientPackage(), USkeleton::StaticClass(), TEXT("SK_AuthoredReferenceProof"));
    USkeleton* Skeleton = DuplicateObject<USkeleton>(Baked->GetSkeleton(), GetTransientPackage(), SkeletonName);
    const USkeleton* Source = Reference->GetSkeleton();
    const FReferenceSkeleton& TargetRef = Skeleton->GetReferenceSkeleton();
    const FReferenceSkeleton& SourceRef = Source->GetReferenceSkeleton();
    const TArray<FTransform>& SourceTransforms = Reference->GetRetargetTransforms();
    FReferencePose Pose;
    Pose.PoseName = TEXT("CarnivalAuthoredBodyProof");
    Pose.ReferencePose = TargetRef.GetRefBonePose();
    int32 Matched = 0;
    for (int32 I = 0; I < TargetRef.GetNum(); ++I)
    {
        const int32 SourceIndex = SourceRef.FindBoneIndex(TargetRef.GetBoneName(I));
        if (!SourceTransforms.IsValidIndex(SourceIndex)) continue;
        Pose.ReferencePose[I] = SourceTransforms[SourceIndex];
        if (CopyTranslationModes) Skeleton->SetBoneTranslationRetargetingMode(I, Source->GetBoneTranslationRetargetingMode(SourceIndex), false);
        ++Matched;
    }
    if (Matched < 50)
    {
        OutError = TEXT("Too few authored body transforms for a scoped reference-pose proof.");
        return nullptr;
    }
    Skeleton->AnimRetargetSources.Add(Pose.PoseName, Pose);
    Skeleton->AddCompatibleSkeleton(Baked->GetSkeleton());
    const FName SequenceName = MakeUniqueObjectName(GetTransientPackage(), UAnimSequence::StaticClass(), TEXT("AS_AuthoredReferenceProof"));
    UAnimSequence* Proof = DuplicateObject<UAnimSequence>(Baked, GetTransientPackage(), SequenceName);
    Proof->SetSkeleton(Skeleton);
    Proof->RetargetSource = Pose.PoseName;
    Proof->PostEditChange();
    return Proof;
}

static UAnimSequence* SampleBodyAnimation(UAnimSequence* Reference, USkeleton* Skeleton,
    UAnimSequence* Settings, UObject* Outer, FName SequenceName, FString& OutError, bool IncludeConstantSourceBones = false)
{
    OutError.Reset();
    if (!Skeleton || !Settings || !Reference || !Reference->GetSkeleton())
    {
        OutError = TEXT("Sampling requires source, settings and target skeleton.");
        return nullptr;
    }
    const int32 NumFrames = Reference->GetNumberOfSampledKeys();
    const FFrameRate FrameRate = Reference->GetSamplingFrameRate();
    const IAnimationDataModel* SourceModel = Reference->GetDataModelInterface().GetInterface();
    if (!SourceModel || NumFrames < 2 || !FrameRate.IsValid() || Reference->IsValidAdditive())
    {
        OutError = TEXT("Sampled conversion requires a valid non-additive source animation data model.");
        return nullptr;
    }
    Reference->WaitOnExistingCompression(true);
    if (!Reference->Notifies.IsEmpty())
    {
        OutError = TEXT("Sampled body conversion does not yet support notify-bearing source clips.");
        return nullptr;
    }
    const FReferenceSkeleton& Ref = Skeleton->GetReferenceSkeleton();
    TArray<FName> Names; SourceModel->GetBoneTrackNames(Names);
    TSet<FName> AuthoredNames; for (FName Name : Names) AuthoredNames.Add(Name);
    const FReferenceSkeleton& SourceRef = Reference->GetSkeleton()->GetReferenceSkeleton();
    for (int32 I = 0; I < SourceRef.GetRawBoneNum(); ++I) Names.AddUnique(SourceRef.GetBoneName(I));
    Names.RemoveAll([&Ref](FName Name) { return Ref.FindBoneIndex(Name) == INDEX_NONE; });
    if (Names.Num() < 50)
    {
        OutError = TEXT("Too few matching source body tracks for sampled conversion.");
        return nullptr;
    }
    TArray<FBoneIndexType> BoneIndices;
    for (int32 I = 0; I < Ref.GetNum(); ++I) BoneIndices.Add(static_cast<FBoneIndexType>(I));
    FBoneContainer BoneContainer(BoneIndices, UE::Anim::FCurveFilterSettings(), *Skeleton);
    TMap<FName,TArray<FVector3f>> Positions, Scales;
    TMap<FName,TArray<FQuat4f>> Rotations;
    for (FName Name : Names)
    {
        Positions.Add(Name).Reserve(NumFrames);
        Rotations.Add(Name).Reserve(NumFrames);
        Scales.Add(Name).Reserve(NumFrames);
    }
    for (int32 Frame = 0; Frame < NumFrames; ++Frame)
    {
        FMemMark Mark(FMemStack::Get());
        FCompactPose Pose; Pose.SetBoneContainer(&BoneContainer);
        FBlendedCurve Curves; Curves.InitFrom(BoneContainer);
        UE::Anim::FStackAttributeContainer Attributes;
        FAnimationPoseData Data(Pose, Curves, Attributes);
        Reference->GetAnimationPose(Data, FAnimExtractContext(FrameRate.AsSeconds(FFrameTime(Frame))));
        for (FName Name : Names)
        {
            const FCompactPoseBoneIndex Index = BoneContainer.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(Name));
            const FTransform& Transform = Pose[Index];
            Positions[Name].Add(FVector3f(Transform.GetTranslation()));
            Rotations[Name].Add(FQuat4f(Transform.GetRotation()));
            Scales[Name].Add(FVector3f(Transform.GetScale3D()));
        }
    }
    if (!IncludeConstantSourceBones)
    {
        Names.RemoveAll([&](FName Name)
        {
            if (AuthoredNames.Contains(Name)) return false;
            for (int32 Frame = 1; Frame < NumFrames; ++Frame)
            {
                if (!Positions[Name][Frame].Equals(Positions[Name][0], 0.0001f)
                    || !Rotations[Name][Frame].Equals(Rotations[Name][0], 0.00001f)
                    || !Scales[Name][Frame].Equals(Scales[Name][0], 0.00001f)) return false;
            }
            return true;
        });
    }
    UAnimSequence* Proof = NewObject<UAnimSequence>(Outer, SequenceName, Outer == GetTransientPackage() ? RF_Transient : RF_Public);
    Proof->SetSkeleton(Skeleton);
    Proof->BoneCompressionSettings = Settings->BoneCompressionSettings;
    Proof->CurveCompressionSettings = Settings->CurveCompressionSettings;
    Proof->bEnableRootMotion = Settings->bEnableRootMotion;
    Proof->bForceRootLock = Settings->bForceRootLock;
    Proof->RootMotionRootLock = Settings->RootMotionRootLock;
    IAnimationDataController& Controller = Proof->GetController();
    Controller.OpenBracket(NSLOCTEXT("CarnivalCrowd", "SampleBodyConversion", "Sample body animation into crowd bone spaces"));
    Controller.InitializeModel();
    Controller.SetFrameRate(FrameRate);
    Controller.SetNumberOfFrames(FFrameNumber(NumFrames - 1));
    for (FName Name : Names)
    {
        Controller.AddBoneCurve(Name);
        Controller.SetBoneTrackKeys(Name, Positions[Name], Rotations[Name], Scales[Name]);
    }
    for (const FFloatCurve& Curve : SourceModel->GetFloatCurves())
    {
        const FAnimationCurveIdentifier Id(Curve.GetName(), ERawCurveTrackTypes::RCT_Float);
        Controller.AddCurve(Id, Curve.GetCurveTypeFlags());
        Controller.SetCurveKeys(Id, Curve.FloatCurve.GetCopyOfKeys());
    }
    Controller.NotifyPopulated();
    Controller.CloseBracket();
    Proof->RateScale = Settings->RateScale;
    Proof->AuthoredSyncMarkers = Reference->AuthoredSyncMarkers;
    Proof->AnimNotifyTracks = Reference->AnimNotifyTracks;
    Proof->RefreshCacheData();
    Proof->PostEditChange();
    return Proof;
}

UAnimSequence* UCarnivalCrowdMaterialEditorLibrary::MakeAnimationSpaceConversionProof(UAnimSequence* Baked,
    UAnimSequence* Reference, FString& OutError, bool IncludeConstantSourceBones)
{
    OutError.Reset();
    if (!Baked || !Baked->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Baked->GetSkeleton())
    {
        OutError = TEXT("Space-conversion proof requires an owned candidate clip.");
        return nullptr;
    }
    const FName SkeletonName = MakeUniqueObjectName(GetTransientPackage(), USkeleton::StaticClass(), TEXT("SK_SpaceConversionProof"));
    USkeleton* Skeleton = DuplicateObject<USkeleton>(Baked->GetSkeleton(), GetTransientPackage(), SkeletonName);
    Skeleton->AddCompatibleSkeleton(Baked->GetSkeleton());
    const FName SequenceName = MakeUniqueObjectName(GetTransientPackage(), UAnimSequence::StaticClass(), TEXT("AS_SpaceConversionProof"));
    return SampleBodyAnimation(Reference, Skeleton, Baked, GetTransientPackage(), SequenceName, OutError, IncludeConstantSourceBones);
}

int32 UCarnivalCrowdMaterialEditorLibrary::RestoreCandidateWalkSyncMarkers(UAnimSequence* Source,
    UAnimSequence* Candidate, FString& OutError)
{
    OutError.Reset();
    if (!Source || !Candidate || Source->GetName() != TEXT("AS_Walk")
        || (Candidate->GetName() != TEXT("AS_Walk") && Candidate->GetName() != TEXT("AS_Input_Walk"))
        || !Source->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/G1Parts/"))
        || !Candidate->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/G1PartsRetargeted/"))
        || !Source->Notifies.IsEmpty() || !Candidate->Notifies.IsEmpty()
        || Source->AuthoredSyncMarkers.Num() != 6 || !Candidate->AuthoredSyncMarkers.IsEmpty()
        || FMath::Abs(Source->GetPlayLength() - Candidate->GetPlayLength()) > 0.0001)
    {
        OutError = TEXT("Marker repair requires the diagnosed original/converted G1 shared walk clips, six missing markers and no notify events.");
        return 0;
    }
    Candidate->Modify();
    Candidate->AuthoredSyncMarkers = Source->AuthoredSyncMarkers;
    Candidate->AnimNotifyTracks = Source->AnimNotifyTracks;
    Candidate->RefreshCacheData();
    Candidate->MarkPackageDirty();
    return Candidate->AuthoredSyncMarkers.Num();
}

FString UCarnivalCrowdMaterialEditorLibrary::DescribeAnimationPoseAgreement(USkeletalMesh* Mesh,
    UAnimSequence* Source, UAnimSequence* Candidate, int32 Samples, FString& OutError, bool NormalizeUnanimatedSourceBones)
{
    OutError.Reset();
    if (!Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Source || !Candidate || Samples < 2 || Samples > 256
        || FMath::Abs(Source->GetPlayLength() - Candidate->GetPlayLength()) > 0.0001)
    {
        OutError = TEXT("Pose agreement requires a candidate mesh, equal-duration clips and 2-256 samples.");
        return TEXT("{}");
    }
    Source->WaitOnExistingCompression(true);
    Candidate->WaitOnExistingCompression(true);
    TSet<FName> SourceCompressedTracks;
    {
        const auto Compressed = Source->GetCompressedData();
        const FReferenceSkeleton& SourceRef = Source->GetSkeleton()->GetReferenceSkeleton();
        for (const FTrackToSkeletonMap& Track : Compressed.Get().CompressedTrackToSkeletonMapTable)
        {
            if (SourceRef.IsValidIndex(Track.BoneTreeIndex)) SourceCompressedTracks.Add(SourceRef.GetBoneName(Track.BoneTreeIndex));
        }
    }
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    const int32 NumBones = Ref.GetRawBoneNum();
    TArray<FBoneIndexType> Indices;
    for (int32 I = 0; I < NumBones; ++I) Indices.Add(static_cast<FBoneIndexType>(I));
    FBoneContainer Container(Indices, UE::Anim::FCurveFilterSettings(), *Mesh);
    TArray<double> MaximumErrors; MaximumErrors.Init(0.0, NumBones);
    TArray<double> MaximumRotationErrors; MaximumRotationErrors.Init(0.0, NumBones);
    double Maximum = 0.0;
    double MaximumRotation = 0.0;
    FName WorstBone;
    FName WorstRotationBone;
    for (int32 Sample = 0; Sample < Samples; ++Sample)
    {
        const double Time = Source->GetPlayLength() * Sample / (Samples - 1);
        TArray<FVector> Positions[2];
        TArray<FQuat> Rotations[2];
        for (int32 SequenceIndex = 0; SequenceIndex < 2; ++SequenceIndex)
        {
            FMemMark Mark(FMemStack::Get());
            FCompactPose Pose; Pose.SetBoneContainer(&Container);
            FBlendedCurve Curves; Curves.InitFrom(Container);
            UE::Anim::FStackAttributeContainer Attributes;
            FAnimationPoseData Data(Pose, Curves, Attributes);
            (SequenceIndex == 0 ? Source : Candidate)->GetAnimationPose(Data, FAnimExtractContext(Time));
            if (SequenceIndex == 0 && NormalizeUnanimatedSourceBones)
            {
                for (int32 I = 0; I < NumBones; ++I)
                {
                    if (SourceCompressedTracks.Contains(Ref.GetBoneName(I))) continue;
                    const FCompactPoseBoneIndex Index = Container.MakeCompactPoseIndex(FMeshPoseBoneIndex(I));
                    Pose[Index] = Container.GetRefPoseTransform(Index);
                }
            }
            TArray<FTransform> Global; Global.SetNum(NumBones);
            for (int32 I = 0; I < NumBones; ++I)
            {
                const FCompactPoseBoneIndex Index = Container.MakeCompactPoseIndex(FMeshPoseBoneIndex(I));
                const int32 Parent = Ref.GetParentIndex(I);
                Global[I] = Parent == INDEX_NONE ? Pose[Index] : Pose[Index] * Global[Parent];
                Positions[SequenceIndex].Add(Global[I].GetTranslation());
                Rotations[SequenceIndex].Add(Global[I].GetRotation().GetNormalized());
            }
        }
        for (int32 I = 0; I < NumBones; ++I)
        {
            const double Error = FVector::Distance(Positions[0][I], Positions[1][I]);
            MaximumErrors[I] = FMath::Max(MaximumErrors[I], Error);
            if (Error > Maximum) { Maximum = Error; WorstBone = Ref.GetBoneName(I); }
            const double RotationError = FMath::RadiansToDegrees(Rotations[0][I].AngularDistance(Rotations[1][I]));
            MaximumRotationErrors[I] = FMath::Max(MaximumRotationErrors[I], RotationError);
            if (RotationError > MaximumRotation) { MaximumRotation = RotationError; WorstRotationBone = Ref.GetBoneName(I); }
        }
    }
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("mesh"), Mesh->GetPathName());
    Result->SetStringField(TEXT("source"), Source->GetPathName());
    Result->SetStringField(TEXT("candidate"), Candidate->GetPathName());
    Result->SetNumberField(TEXT("samples"), Samples);
    Result->SetBoolField(TEXT("source_unanimated_bones_restored_to_mesh_reference"), NormalizeUnanimatedSourceBones);
    Result->SetNumberField(TEXT("source_compressed_track_count"), SourceCompressedTracks.Num());
    Result->SetNumberField(TEXT("bone_count"), NumBones);
    Result->SetNumberField(TEXT("duration"), Source->GetPlayLength());
    Result->SetNumberField(TEXT("maximum_bone_position_error_cm"), Maximum);
    Result->SetStringField(TEXT("worst_bone"), WorstBone.ToString());
    Result->SetNumberField(TEXT("maximum_bone_rotation_error_degrees"), MaximumRotation);
    Result->SetStringField(TEXT("worst_rotation_bone"), WorstRotationBone.ToString());
    Result->SetBoolField(TEXT("mesh_uses_compatible_source_retarget_modes"), Mesh->GetSkeleton()->GetUseRetargetModesFromCompatibleSkeleton());
    Result->SetNumberField(TEXT("worst_target_translation_mode"), static_cast<int32>(Mesh->GetSkeleton()->GetBoneTranslationRetargetingMode(Mesh->GetSkeleton()->GetReferenceSkeleton().FindBoneIndex(WorstBone))));
    Result->SetBoolField(TEXT("worst_source_has_track"), Source->GetDataModelInterface()->IsValidBoneTrackName(WorstBone));
    Result->SetBoolField(TEXT("worst_source_has_compressed_track"), SourceCompressedTracks.Contains(WorstBone));
    Result->SetBoolField(TEXT("worst_candidate_has_track"), Candidate->GetDataModelInterface()->IsValidBoneTrackName(WorstBone));
    Result->SetBoolField(TEXT("worst_source_has_skeleton_bone"), Source->GetSkeleton()->GetReferenceSkeleton().FindBoneIndex(WorstBone) != INDEX_NONE);
    TArray<FName> CandidateNames; Candidate->GetDataModelInterface()->GetBoneTrackNames(CandidateNames);
    TArray<TSharedPtr<FJsonValue>> Extras;
    for (FName Name : CandidateNames)
    {
        if (!Source->GetDataModelInterface()->IsValidBoneTrackName(Name)) Extras.Add(MakeShared<FJsonValueString>(Name.ToString()));
    }
    Result->SetArrayField(TEXT("extra_candidate_tracks"), Extras);
    int32 WeightedVertexCount = 0;
    double MaximumWeight = 0.0, MaximumWeightedBoneError = 0.0;
    FName WorstWeightedBone;
    const int32 WorstMeshBone = Ref.FindBoneIndex(WorstBone);
    const FSkeletalMeshModel* Imported = Mesh->GetImportedModel();
    if (Imported && !Imported->LODModels.IsEmpty())
    {
        for (const FSkelMeshSection& Section : Imported->LODModels[0].Sections)
        {
            for (const FSoftSkinVertex& Vertex : Section.SoftVertices)
            {
                bool UsesWorst = false;
                for (int32 Influence = 0; Influence < MAX_TOTAL_INFLUENCES; ++Influence)
                {
                    const int32 LocalBone = Vertex.InfluenceBones[Influence];
                    if (!Vertex.InfluenceWeights[Influence] || !Section.BoneMap.IsValidIndex(LocalBone)) continue;
                    const int32 Bone = Section.BoneMap[LocalBone];
                    if (MaximumErrors.IsValidIndex(Bone) && MaximumErrors[Bone] > MaximumWeightedBoneError)
                    {
                        MaximumWeightedBoneError = MaximumErrors[Bone];
                        WorstWeightedBone = Ref.GetBoneName(Bone);
                    }
                    if (Bone == WorstMeshBone)
                    {
                        UsesWorst = true;
                        MaximumWeight = FMath::Max(MaximumWeight, Vertex.InfluenceWeights[Influence] / 65535.0);
                    }
                }
                if (UsesWorst) ++WeightedVertexCount;
            }
        }
    }
    Result->SetNumberField(TEXT("worst_bone_weighted_vertices_lod0"), WeightedVertexCount);
    Result->SetNumberField(TEXT("worst_bone_maximum_weight_lod0"), MaximumWeight);
    Result->SetNumberField(TEXT("maximum_weighted_bone_position_error_cm_lod0"), MaximumWeightedBoneError);
    Result->SetStringField(TEXT("worst_weighted_bone_lod0"), WorstWeightedBone.ToString());
    TSharedRef<FJsonObject> Landmarks = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> LandmarkRotations = MakeShared<FJsonObject>();
    for (FName Name : {FName(TEXT("root")), FName(TEXT("pelvis")), FName(TEXT("head")), FName(TEXT("hand_l")), FName(TEXT("hand_r")), FName(TEXT("foot_l")), FName(TEXT("foot_r"))})
    {
        const int32 Index = Ref.FindBoneIndex(Name);
        if (MaximumErrors.IsValidIndex(Index)) Landmarks->SetNumberField(Name.ToString(), MaximumErrors[Index]);
        if (MaximumRotationErrors.IsValidIndex(Index)) LandmarkRotations->SetNumberField(Name.ToString(), MaximumRotationErrors[Index]);
    }
    Result->SetObjectField(TEXT("landmark_maximum_errors_cm"), Landmarks);
    Result->SetObjectField(TEXT("landmark_maximum_rotation_errors_degrees"), LandmarkRotations);
    FString Text; FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Text)); return Text;
}

FString UCarnivalCrowdMaterialEditorLibrary::DescribeSkeletalComponentPose(USkeletalMeshComponent* Component)
{
    const USkeletalMesh* Mesh = Component ? Component->GetSkeletalMeshAsset() : nullptr;
    if (!Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/"))) return TEXT("{}");
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("component"), Component->GetPathName());
    Result->SetStringField(TEXT("mesh"), Mesh->GetPathName());
    Result->SetStringField(TEXT("skeleton"), Mesh->GetSkeleton() ? Mesh->GetSkeleton()->GetPathName() : FString());
    Result->SetStringField(TEXT("transform"), Component->GetComponentTransform().ToString());
    Result->SetBoolField(TEXT("visible"), Component->IsVisible());
    for (FName Flag : {FName(TEXT("CastShadow")), FName(TEXT("bCastHiddenShadow"))})
    {
        const FBoolProperty* Property = CastField<FBoolProperty>(Component->GetClass()->FindPropertyByName(Flag));
        if (Property) Result->SetBoolField(Flag.ToString(), Property->GetPropertyValue_InContainer(Component));
    }
    Result->SetStringField(TEXT("tick_policy"), StaticEnum<EVisibilityBasedAnimTickOption>()->GetNameStringByValue(static_cast<int64>(Component->VisibilityBasedAnimTickOption)));
    const UAnimSingleNodeInstance* Single = Component->GetSingleNodeInstance();
    UAnimationAsset* Animation = Single ? const_cast<UAnimSingleNodeInstance*>(Single)->GetCurrentAsset() : nullptr;
    Result->SetStringField(TEXT("current_animation"), Animation ? Animation->GetPathName() : FString());
    Result->SetStringField(TEXT("animation_skeleton"), Animation && Animation->GetSkeleton() ? Animation->GetSkeleton()->GetPathName() : FString());
    Result->SetNumberField(TEXT("animation_time"), Single ? Single->GetCurrentTime() : 0.0);
    Result->SetNumberField(TEXT("animation_rate"), Single ? Single->GetPlayRate() : 0.0);
    const UAnimSequence* Sequence = Cast<UAnimSequence>(Animation);
    Result->SetStringField(TEXT("retarget_source_mesh"), Sequence ? Sequence->GetRetargetSourceAsset().ToString() : FString());
    Result->SetStringField(TEXT("retarget_source_name"), Sequence ? Sequence->RetargetSource.ToString() : FString());
    Result->SetNumberField(TEXT("retarget_transform_count"), Sequence ? Sequence->GetRetargetTransforms().Num() : 0);
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    TArray<TSharedPtr<FJsonValue>> Bones;
    for (FName Name : {FName(TEXT("root")), FName(TEXT("pelvis")), FName(TEXT("head")), FName(TEXT("hand_l")), FName(TEXT("hand_r")), FName(TEXT("foot_l")), FName(TEXT("foot_r"))})
    {
        const int32 Index = Ref.FindBoneIndex(Name);
        if (Index == INDEX_NONE) continue;
        FTransform Reference = Ref.GetRefBonePose()[Index];
        for (int32 Parent = Ref.GetParentIndex(Index); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent)) Reference *= Ref.GetRefBonePose()[Parent];
        const FVector RefWorld = Component->GetComponentTransform().TransformPosition(Reference.GetLocation());
        const FVector Posed = Component->GetSocketLocation(Name);
        TSharedRef<FJsonObject> Bone = MakeShared<FJsonObject>();
        Bone->SetStringField(TEXT("bone"), Name.ToString());
        for (const auto& Pair : {TPair<FString,const USkeleton*>(TEXT("mesh_skeleton_mode"), Mesh->GetSkeleton()), TPair<FString,const USkeleton*>(TEXT("animation_skeleton_mode"), Animation ? Animation->GetSkeleton() : nullptr)})
        {
            if (!Pair.Value) continue;
            const int32 SkeletonIndex = Pair.Value->GetReferenceSkeleton().FindBoneIndex(Name);
            if (SkeletonIndex != INDEX_NONE) Bone->SetNumberField(Pair.Key, static_cast<int32>(Pair.Value->GetBoneTranslationRetargetingMode(SkeletonIndex)));
        }
        auto Vector = [](const FVector& V) { return TArray<TSharedPtr<FJsonValue>>{MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)}; };
        if (Sequence && Sequence->GetSkeleton())
        {
            const int32 AnimationBone = Sequence->GetSkeleton()->GetReferenceSkeleton().FindBoneIndex(Name);
            if (Sequence->GetRetargetTransforms().IsValidIndex(AnimationBone))
            {
                Bone->SetArrayField(TEXT("animation_authored_local"), Vector(Sequence->GetRetargetTransforms()[AnimationBone].GetTranslation()));
                Bone->SetArrayField(TEXT("animation_skeleton_local"), Vector(Sequence->GetSkeleton()->GetReferenceSkeleton().GetRefBonePose()[AnimationBone].GetTranslation()));
            }
        }
        Bone->SetArrayField(TEXT("reference_world"), Vector(RefWorld));
        Bone->SetArrayField(TEXT("posed_world"), Vector(Posed));
        Bone->SetArrayField(TEXT("delta"), Vector(Posed - RefWorld));
        Bones.Add(MakeShared<FJsonValueObject>(Bone));
    }
    Result->SetArrayField(TEXT("bones"), Bones);
    FString Text; FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Text)); return Text;
}

FString UCarnivalCrowdMaterialEditorLibrary::DescribeInstanceSelections(UMetaHumanInstance* Instance)
{
    if (!Instance) return TEXT("{}");
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("instance"), Instance->GetPathName());
    Result->SetStringField(TEXT("collection"), Instance->GetMetaHumanCollection() ? Instance->GetMetaHumanCollection()->GetPathName() : FString());
    TArray<TSharedPtr<FJsonValue>> Selections;
    for (const auto& Pinned : Instance->ToPinnedSlotSelections(EMetaHumanUnusedSlotBehavior::Unpinned))
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("slot"), Pinned.Selection.SlotName.ToString());
        Row->SetStringField(TEXT("key"), Pinned.Selection.SelectedItem.ToDebugString());
        Row->SetBoolField(TEXT("empty"), Pinned.Selection.SelectedItem.IsNull());
        Row->SetBoolField(TEXT("root"), Pinned.Selection.ParentItemPath.IsEmpty());
        Selections.Add(MakeShared<FJsonValueObject>(Row));
    }
    Result->SetArrayField(TEXT("selections"), Selections);
    FString Parameters;
    for (FName Field : {FName(TEXT("OverriddenInstanceParameters")), FName(TEXT("OverriddenCollectionInstanceParameters"))})
    {
        const FProperty* Property = Instance->GetClass()->FindPropertyByName(Field);
        if (!Property) return TEXT("{}");
        Property->ExportTextItem_Direct(Parameters, Property->ContainerPtrToValuePtr<void>(Instance), nullptr, nullptr, PPF_None);
    }
    FTCHARToUTF8 Bytes(*Parameters);
    FSHAHash Hash; FSHA1::HashBuffer(Bytes.Get(), Bytes.Length(), Hash.Hash);
    Result->SetStringField(TEXT("parameter_overrides_sha1"), Hash.ToString());
    Result->SetNumberField(TEXT("parameter_overrides_text_length"), Parameters.Len());
    FString Text; FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Text));
    return Text;
}

UMetaHumanCollection* UCarnivalCrowdMaterialEditorLibrary::BuildClothingFamilyCollection(UMetaHumanCollection* Source,
    const FString& PackageName, bool CompleteOutfitsOnly, bool ConvertBodyAnimations, FString& OutError, int32 BodySourceLOD)
{
    OutError.Reset();
    if (!Source || !Source->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/Collections/"))
        || !PackageName.StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !FPackageName::IsValidLongPackageName(PackageName) || FPackageName::DoesPackageExist(PackageName)
        || FindObject<UPackage>(nullptr, *PackageName))
    {
        OutError = TEXT("A clothing family requires an owned source and a fresh candidate package.");
        return nullptr;
    }
    UPackage* Package = CreatePackage(*PackageName);
    auto* Candidate = NewObject<UMetaHumanCollection>(Package,
        *FPackageName::GetLongPackageAssetName(PackageName), RF_Public | RF_Standalone);
    Candidate->CopyContentsFrom(Source);
    Candidate->SetQuality(Source->GetQuality());
    auto* Runtime = Cast<UMetaHumanCrowdPipeline>(Candidate->GetMutablePipeline());
    auto* Editor = Runtime ? Cast<UMetaHumanCrowdEditorPipeline>(Runtime->GetMutableEditorPipeline()) : nullptr;
    if (!Editor || !Editor->TargetSkeleton)
    {
        OutError = TEXT("Source has no configured crowd skeleton.");
        return nullptr;
    }
    Editor->TargetSkeleton = DuplicateObject<USkeleton>(Editor->TargetSkeleton, Candidate, TEXT("SK_ClothingFamily"));
    if (BodySourceLOD != -1)
    {
        // Scoped source-preserving diagnostic for garments whose source bundle has
        // only LOD 0. Do not silently substitute a missing garment or change a source
        // collection. This candidate still requires visual/GPU/performance acceptance.
        if (BodySourceLOD != 0 || Editor->ActorBodyLODs.IsEmpty() || Editor->InstancedBodyLODs.IsEmpty())
        { OutError = TEXT("Body LOD diagnostic requires LOD 0 and configured actor/instanced body settings."); return nullptr; }
        Editor->ActorBodyLODs.SetNum(1); Editor->ActorBodyLODs[0].SourceLOD = 0;
        Editor->InstancedBodyLODs.SetNum(1); Editor->InstancedBodyLODs[0].SourceLOD = 0;
    }
    if (ConvertBodyAnimations)
    {
        if (!Editor->AnimationConfig || Editor->AnimationConfig->AnimationsToBake.IsEmpty())
        {
            OutError = TEXT("Retargeted family requires an animation configuration.");
            return nullptr;
        }
        Editor->AnimationConfig = DuplicateObject<UMetaHumanCrowdAnimationConfig>(Editor->AnimationConfig, Candidate, TEXT("AC_ConvertedBodyInputs"));
        for (FMetaHumanCrowdBakeAnimationData& Entry : Editor->AnimationConfig->AnimationsToBake)
        {
            if (!Entry.IsValid() || Entry.bUseMergedAnimation || Entry.FaceAnimSequence)
            {
                OutError = TEXT("Scoped body conversion supports valid body-only input entries.");
                return nullptr;
            }
            UAnimSequence* Input = SampleBodyAnimation(Entry.BodyAnimSequence, Editor->TargetSkeleton,
                Entry.BodyAnimSequence, Candidate, *FString::Printf(TEXT("AS_Input_%s"), *Entry.Name.ToString()), OutError);
            if (!Input) return nullptr;
            Entry.BodyAnimSequence = Input;
        }
    }
    const TArray<FMetaHumanCharacterPaletteItem> Items = Candidate->GetItems();
    int32 ClothingCount = 0;
    for (const FMetaHumanCharacterPaletteItem& Item : Items)
    {
        const bool Complete = Item.SlotName == TEXT("Outfits");
        const bool Part = Item.SlotName == TEXT("Top Garment") || Item.SlotName == TEXT("Bottom Garment") || Item.SlotName == TEXT("Shoes");
        if ((CompleteOutfitsOnly && Part) || (!CompleteOutfitsOnly && Complete))
        {
            if (!Candidate->TryRemoveItem(Item.GetItemKey()))
            {
                OutError = TEXT("Could not remove the other clothing composition from the candidate.");
                return nullptr;
            }
        }
        else if (Complete || Part) ++ClothingCount;
    }
    if (ClothingCount == 0)
    {
        OutError = TEXT("The requested clothing family has no items.");
        return nullptr;
    }
    Candidate->RefreshBuildCacheGuid();
    EMetaHumanBuildStatus Status = EMetaHumanBuildStatus::Failed;
    Candidate->Build(FInstancedStruct(), UMetaHumanCollection::FOnBuildComplete::CreateLambda(
        [&Status](EMetaHumanBuildStatus Result) { Status = Result; }));
    if (Status != EMetaHumanBuildStatus::Succeeded)
    {
        OutError = TEXT("SDK failed to build the clothing family; inspect the editor log.");
        return nullptr;
    }
    Candidate->MarkPackageDirty();
    return Candidate;
}

UMetaHumanInstance* UCarnivalCrowdMaterialEditorLibrary::CloneInstanceForClothingFamily(UMetaHumanInstance* Source,
    UMetaHumanCollection* Collection, const FString& PackageName, FString& OutError)
{
    OutError.Reset();
    if (!Source || !Source->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/Instances/ExpandedFinal2/"))
        || !Collection || !Collection->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !Collection->GetBuiltData().IsValid()
        || !PackageName.StartsWith(TEXT("/Game/Carnival/Crowd/ClothingFamilies/"))
        || !FPackageName::IsValidLongPackageName(PackageName) || FPackageName::DoesPackageExist(PackageName)
        || FindObject<UPackage>(nullptr, *PackageName))
    {
        OutError = TEXT("Instance cloning requires an original owned appearance, a built clothing family and a fresh package.");
        return nullptr;
    }
    for (const FMetaHumanPinnedSlotSelection& Pinned : Source->ToPinnedSlotSelections(EMetaHumanUnusedSlotBehavior::Unpinned))
    {
        const auto& Selection = Pinned.Selection;
        if (Selection.SelectedItem.IsNull()) continue;
        if (!Selection.ParentItemPath.IsEmpty() || !Collection->GetItems().ContainsByPredicate(
            [&Selection](const FMetaHumanCharacterPaletteItem& Item)
            { return Item.SlotName == Selection.SlotName && Item.GetItemKey() == Selection.SelectedItem; }))
        {
            OutError = FString::Printf(TEXT("Candidate cannot preserve the selected item in %s."), *Selection.SlotName.ToString());
            return nullptr;
        }
    }
    UPackage* Package = CreatePackage(*PackageName);
    auto* Instance = NewObject<UMetaHumanInstance>(Package,
        *FPackageName::GetLongPackageAssetName(PackageName), RF_Public | RF_Standalone);
    Instance->CopyContentsFrom(Source);
    Instance->SetMetaHumanCollection(Collection);
    Instance->MarkPackageDirty();
    return Instance;
}

UMetaHumanCollection* UCarnivalCrowdMaterialEditorLibrary::BuildBodyOwnershipProof(UMetaHumanCollection* Source, UMetaHumanInstance* SelectionSource,
    const FString& PackageName, bool IncludeCompleteOutfits, FString& OutError)
{
    OutError.Reset();
    if (!Source || !SelectionSource || SelectionSource->GetMetaHumanCollection() != Source
        || !Source->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/Collections/"))
        || !PackageName.StartsWith(TEXT("/Game/Carnival/Crowd/BodySurfaceProof/"))
        || !FPackageName::IsValidLongPackageName(PackageName) || FPackageName::DoesPackageExist(PackageName)
        || FindObject<UPackage>(nullptr, *PackageName))
    {
        OutError = TEXT("Ownership proof requires an owned source collection and a fresh proof package.");
        return nullptr;
    }
    TMap<FName, FMetaHumanPaletteItemKey> SelectedParts;
    for (FName Slot : { FName(TEXT("Top Garment")), FName(TEXT("Bottom Garment")), FName(TEXT("Shoes")) })
    {
        FMetaHumanPaletteItemKey Key;
        if (!SelectionSource->TryGetAnySlotSelection(Slot, Key) || Key.IsNull())
        {
            OutError = FString::Printf(TEXT("Source guest has no selection in %s."), *Slot.ToString());
            return nullptr;
        }
        SelectedParts.Add(Slot, Key);
    }
    UPackage* Package = CreatePackage(*PackageName);
    UMetaHumanCollection* Proof = NewObject<UMetaHumanCollection>(Package,
        *FPackageName::GetLongPackageAssetName(PackageName), RF_Public | RF_Standalone);
    Proof->CopyContentsFrom(Source);
    Proof->SetQuality(Source->GetQuality());
    auto* Runtime = Cast<UMetaHumanCrowdPipeline>(Proof->GetMutablePipeline());
    auto* Editor = Runtime ? Cast<UMetaHumanCrowdEditorPipeline>(Runtime->GetMutableEditorPipeline()) : nullptr;
    if (!Editor || !Editor->TargetSkeleton)
    {
        OutError = TEXT("Source has no crowd editor pipeline or target skeleton.");
        return nullptr;
    }
    Editor->TargetSkeleton = DuplicateObject<USkeleton>(Editor->TargetSkeleton, Proof, TEXT("SK_DeanOwnershipProof"));
    const TArray<FMetaHumanCharacterPaletteItem> Items = Proof->GetItems();
    int32 KeptHead = 0, KeptBody = 0, KeptParts = 0, KeptComplete = 0;
    for (const FMetaHumanCharacterPaletteItem& Item : Items)
    {
        UObject* Principal = Item.LoadPrincipalAssetSynchronous();
        const FName Name = Principal ? Principal->GetFName() : NAME_None;
        bool Keep = false;
        if (Item.SlotName == UMetaHumanCrowdPipeline::HeadSlotName && Name == TEXT("Dean")) { Keep = true; ++KeptHead; }
        else if (Item.SlotName == UMetaHumanCrowdPipeline::BodySlotName && Name == TEXT("Dean")) { Keep = true; ++KeptBody; }
        else if (const FMetaHumanPaletteItemKey* Selected = SelectedParts.Find(Item.SlotName);
            Selected && Item.GetItemKey() == *Selected) { Keep = true; ++KeptParts; }
        else if (IncludeCompleteOutfits && Item.SlotName == TEXT("Outfits")) { Keep = true; ++KeptComplete; }
        if (!Keep && !Proof->TryRemoveItem(Item.GetItemKey()))
        {
            OutError = TEXT("Could not remove an unrelated item from the proof.");
            return nullptr;
        }
    }
    if (KeptHead != 1 || KeptBody != 1 || KeptParts != 3 || (IncludeCompleteOutfits && KeptComplete == 0))
    {
        OutError = FString::Printf(TEXT("Unexpected proof roster: heads=%d bodies=%d parts=%d complete=%d."), KeptHead, KeptBody, KeptParts, KeptComplete);
        return nullptr;
    }
    Proof->RefreshBuildCacheGuid();
    EMetaHumanBuildStatus Status = EMetaHumanBuildStatus::Failed;
    Proof->Build(FInstancedStruct(), UMetaHumanCollection::FOnBuildComplete::CreateLambda(
        [&Status](EMetaHumanBuildStatus Result) { Status = Result; }));
    if (Status != EMetaHumanBuildStatus::Succeeded)
    {
        OutError = TEXT("SDK failed to build the isolated body ownership proof; inspect its editor log.");
        return nullptr;
    }
    Proof->MarkPackageDirty();
    return Proof;
}

int32 UCarnivalCrowdMaterialEditorLibrary::SelectBodyOwnershipProofClothes(UMetaHumanInstance* Instance, FString& OutError)
{
    OutError.Reset();
    const UMetaHumanCollection* Collection = Instance ? Instance->GetMetaHumanCollection() : nullptr;
    if (!Collection || !Collection->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/BodySurfaceProof/")))
    {
        OutError = TEXT("Clothing selection requires an isolated ownership proof instance.");
        return 0;
    }
    int32 Count = 0;
    for (const FMetaHumanCharacterPaletteItem& Item : Collection->GetItems())
    {
        if (Item.SlotName != TEXT("Top Garment") && Item.SlotName != TEXT("Bottom Garment") && Item.SlotName != TEXT("Shoes")) continue;
        if (!Instance->TryAddSlotSelection(FMetaHumanPipelineSlotSelection(Item.SlotName, Item.GetItemKey())))
        {
            OutError = TEXT("Could not select proof clothing.");
            return Count;
        }
        ++Count;
    }
    Instance->MarkPackageDirty();
    return Count;
}

FString UCarnivalCrowdMaterialEditorLibrary::DescribeCollectionSlots(UMetaHumanCollection* Collection)
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    if (!Collection) return TEXT("{}");
    const UMetaHumanCollectionPipeline* Pipeline = Collection->GetPipeline();
    const UMetaHumanCharacterPipelineSpecification* Spec = nullptr;
    if (Pipeline) Spec = Pipeline->GetSpecification();
    if (!Spec) return TEXT("{}");
    Result->SetStringField(TEXT("collection"), Collection->GetPathName());
    TArray<TSharedPtr<FJsonValue>> Slots;
    for (const auto& Pair : Spec->Slots)
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("slot"), Pair.Key.ToString());
        const TOptional<FName> Real = Spec->ResolveRealSlotName(Pair.Key);
        Row->SetStringField(TEXT("resolved_slot"), Real.IsSet() ? Real.GetValue().ToString() : FString());
        Row->SetStringField(TEXT("build_output"), Pair.Value.BuildOutputStruct ? Pair.Value.BuildOutputStruct->GetPathName() : FString());
        int32 Count = 0;
        for (const FMetaHumanCharacterPaletteItem& Item : Collection->GetItems()) if (Item.SlotName == Pair.Key) ++Count;
        Row->SetNumberField(TEXT("direct_item_count"), Count);
        Slots.Add(MakeShared<FJsonValueObject>(Row));
    }
    Result->SetArrayField(TEXT("slots"), Slots);
    FString Text;
    FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Text));
    return Text;
}

USkeletalMesh* UCarnivalCrowdMaterialEditorLibrary::MakeTrimmedBodyProof(USkeletalMesh* Source,
    const TArray<UMetaHumanWardrobeItem*>& Garments, FString& OutError)
{
    OutError.Reset();
    using namespace UE::MetaHuman::GeometryRemoval;
    if (!Source || !Source->GetPathName().StartsWith(TEXT("/Game/Carnival/Crowd/Collections/")) || Garments.IsEmpty())
    {
        OutError = TEXT("Proof requires an owned crowd body and selected source garments.");
        return nullptr;
    }
    TArray<FHiddenFaceMapTexture> Textures;
    for (const UMetaHumanWardrobeItem* Garment : Garments)
    {
        const UMetaHumanItemEditorPipeline* Pipeline = Garment ? Garment->GetEditorPipeline() : nullptr;
        const FStructProperty* Property = Pipeline ? FindFProperty<FStructProperty>(Pipeline->GetClass(), TEXT("BodyHiddenFaceMapTexture")) : nullptr;
        if (!Property || Property->Struct != FHiddenFaceMapTexture::StaticStruct())
        {
            OutError = TEXT("Every selected garment must provide its original body hidden face map settings.");
            return nullptr;
        }
        const FHiddenFaceMapTexture* Map = Property->ContainerPtrToValuePtr<FHiddenFaceMapTexture>(Pipeline);
        if (!Map->Texture)
        {
            OutError = TEXT("A selected garment has no body hidden face map texture.");
            return nullptr;
        }
        Textures.Add(*Map);
    }
    TArray<FHiddenFaceMapImage> Images;
    FHiddenFaceMapImage Combined;
    FText Failure;
    if (!TryConvertHiddenFaceMapTexturesToImages(Textures, Images, Failure)
        || !TryCombineHiddenFaceMaps(Images, Combined, Failure))
    {
        OutError = Failure.ToString();
        return nullptr;
    }
    TStrongObjectPtr<USkeletalMesh> Proof(DuplicateObject<USkeletalMesh>(Source, GetTransientPackage()));
    for (int32 LOD = 0; LOD < Proof->GetLODNum(); ++LOD)
    {
        if (!RemoveAndShrinkGeometry(Proof.Get(), LOD, Combined))
        {
            OutError = FString::Printf(TEXT("Original garment masks could not trim proof LOD %d."), LOD);
            return nullptr;
        }
    }
    FSkinnedAssetCompilingManager::Get().FinishCompilation({Proof.Get()});
    return Proof.Get();
}

FString UCarnivalCrowdMaterialEditorLibrary::DescribeLoadedMeshSections(USkeletalMesh* Mesh)
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    if (!Mesh) return TEXT("{}");
    Result->SetStringField(TEXT("mesh"), Mesh->GetPathName());
    Result->SetStringField(TEXT("skeleton"), Mesh->GetSkeleton() ? Mesh->GetSkeleton()->GetPathName() : FString());
    Result->SetNumberField(TEXT("reference_bones"), Mesh->GetRefSkeleton().GetNum());
    TArray<TSharedPtr<FJsonValue>> Materials;
    for (const FSkeletalMaterial& Material : Mesh->GetMaterials())
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("slot"), Material.MaterialSlotName.ToString());
        Row->SetStringField(TEXT("imported_slot"), Material.ImportedMaterialSlotName.ToString());
        Row->SetStringField(TEXT("material"), Material.MaterialInterface ? Material.MaterialInterface->GetPathName() : FString());
        Materials.Add(MakeShared<FJsonValueObject>(Row));
    }
    Result->SetArrayField(TEXT("materials"), Materials);
    TArray<TSharedPtr<FJsonValue>> LODs;
    const FSkeletalMeshModel* Model = Mesh->GetImportedModel();
    if (Model) for (int32 LOD = 0; LOD < Model->LODModels.Num(); ++LOD)
    {
        const FSkeletalMeshLODModel& Data = Model->LODModels[LOD];
        const FSkeletalMeshLODInfo* Info = Mesh->GetLODInfo(LOD);
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("lod"), LOD);
        Row->SetNumberField(TEXT("vertices"), Data.NumVertices);
        TArray<TSharedPtr<FJsonValue>> Map;
        if (Info) for (int32 Index : Info->LODMaterialMap) Map.Add(MakeShared<FJsonValueNumber>(Index));
        Row->SetArrayField(TEXT("material_map"), Map);
        TArray<TSharedPtr<FJsonValue>> Sections;
        for (int32 Index = 0; Index < Data.Sections.Num(); ++Index)
        {
            const FSkelMeshSection& Section = Data.Sections[Index];
            TSharedRef<FJsonObject> S = MakeShared<FJsonObject>();
            S->SetNumberField(TEXT("section"), Index);
            S->SetNumberField(TEXT("material_index"), Section.MaterialIndex);
            const int32 Effective = Info && Info->LODMaterialMap.IsValidIndex(Index) && Info->LODMaterialMap[Index] != INDEX_NONE
                ? Info->LODMaterialMap[Index] : Section.MaterialIndex;
            S->SetNumberField(TEXT("mapped_material_index"), Effective);
            S->SetBoolField(TEXT("valid_material"), Mesh->GetMaterials().IsValidIndex(Effective));
            S->SetNumberField(TEXT("triangles"), Section.NumTriangles);
            S->SetNumberField(TEXT("vertices"), Section.NumVertices);
            S->SetBoolField(TEXT("disabled"), Section.bDisabled);
            FBox Bounds(ForceInit);
            uint32 MinWeight = MAX_uint32, MaxWeight = 0;
            int32 ZeroWeights = 0, InvalidInfluences = 0, InvalidBoneMap = 0;
            for (FBoneIndexType Bone : Section.BoneMap) if (Bone >= Mesh->GetRefSkeleton().GetNum()) ++InvalidBoneMap;
            for (const FSoftSkinVertex& Vertex : Section.SoftVertices)
            {
                Bounds += FVector(Vertex.Position);
                uint32 Sum = 0;
                for (int32 Influence = 0; Influence < UE_ARRAY_COUNT(Vertex.InfluenceWeights); ++Influence)
                {
                    Sum += Vertex.InfluenceWeights[Influence];
                    if (Vertex.InfluenceWeights[Influence] && !Section.BoneMap.IsValidIndex(Vertex.InfluenceBones[Influence])) ++InvalidInfluences;
                }
                MinWeight = FMath::Min(MinWeight, Sum); MaxWeight = FMath::Max(MaxWeight, Sum);
                if (Sum == 0) ++ZeroWeights;
            }
            S->SetStringField(TEXT("bounds_min"), Bounds.IsValid ? Bounds.Min.ToString() : FString());
            S->SetStringField(TEXT("bounds_max"), Bounds.IsValid ? Bounds.Max.ToString() : FString());
            S->SetNumberField(TEXT("min_weight_sum"), MinWeight == MAX_uint32 ? 0 : MinWeight);
            S->SetNumberField(TEXT("max_weight_sum"), MaxWeight);
            S->SetNumberField(TEXT("zero_weight_vertices"), ZeroWeights);
            S->SetNumberField(TEXT("invalid_influences"), InvalidInfluences);
            S->SetNumberField(TEXT("invalid_bone_map"), InvalidBoneMap);
            Sections.Add(MakeShared<FJsonValueObject>(S));
        }
        Row->SetArrayField(TEXT("sections"), Sections);
        TArray<TSharedPtr<FJsonValue>> Groups;
        const FMeshDescription* MD = Mesh->GetMeshDescription(LOD);
        if (MD)
        {
            FStaticMeshConstAttributes Attributes(*MD);
            const auto Names = Attributes.GetPolygonGroupMaterialSlotNames();
            for (FPolygonGroupID Group : MD->PolygonGroups().GetElementIDs())
            {
                TSharedRef<FJsonObject> G = MakeShared<FJsonObject>();
                G->SetNumberField(TEXT("id"), Group.GetValue());
                G->SetStringField(TEXT("slot"), Names[Group].ToString());
                G->SetNumberField(TEXT("triangles"), MD->GetPolygonGroupTriangles(Group).Num());
                Groups.Add(MakeShared<FJsonValueObject>(G));
            }
        }
        Row->SetArrayField(TEXT("polygon_groups"), Groups);
        LODs.Add(MakeShared<FJsonValueObject>(Row));
    }
    Result->SetArrayField(TEXT("lods"), LODs);
    FString Text;
    FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Text));
    return Text;
}

FString UCarnivalCrowdMaterialEditorLibrary::GetLoadedMeshStructureDigest(USkeletalMesh* Mesh)
{
    if (!Mesh) return FString();
    FSHA1 Hash;
    auto Value = [&Hash](const auto& V) { Hash.Update(reinterpret_cast<const uint8*>(&V), sizeof(V)); };
    auto String = [&Hash, &Value](const FString& S)
    {
        FTCHARToUTF8 UTF8(*S);
        const int32 Size = UTF8.Length();
        Value(Size);
        Hash.Update(reinterpret_cast<const uint8*>(UTF8.Get()), Size);
    };
    String(Mesh->GetSkeleton() ? Mesh->GetSkeleton()->GetPathName() : FString());
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    Value(Ref.GetNum());
    for (int32 Bone = 0; Bone < Ref.GetNum(); ++Bone)
    {
        String(Ref.GetBoneName(Bone).ToString());
        Value(Ref.GetParentIndex(Bone));
        Value(Ref.GetRefBonePose()[Bone].GetTranslation());
        Value(Ref.GetRefBonePose()[Bone].GetRotation());
        Value(Ref.GetRefBonePose()[Bone].GetScale3D());
    }
    Value(Mesh->GetMaterials().Num());
    for (const FSkeletalMaterial& Material : Mesh->GetMaterials())
    {
        String(Material.MaterialSlotName.ToString());
        String(Material.ImportedMaterialSlotName.ToString());
        String(Material.MaterialInterface ? Material.MaterialInterface->GetPathName() : FString());
    }
    const FSkeletalMeshModel* Model = Mesh->GetImportedModel();
    Value(Model ? Model->LODModels.Num() : INDEX_NONE);
    if (Model)
    {
        for (int32 LOD = 0; LOD < Model->LODModels.Num(); ++LOD)
        {
            const FSkeletalMeshLODModel& Data = Model->LODModels[LOD];
            Value(Data.NumVertices);
            Value(Data.Sections.Num());
            Value(Data.IndexBuffer.Num());
            for (uint32 Index : Data.IndexBuffer) Value(Index);
            const FSkeletalMeshLODInfo* Info = Mesh->GetLODInfo(LOD);
            Value(Info ? Info->LODMaterialMap.Num() : INDEX_NONE);
            if (Info) for (int32 Index : Info->LODMaterialMap) Value(Index);
            for (const FSkelMeshSection& Section : Data.Sections)
            {
                Value(Section.MaterialIndex);
                Value(Section.BaseIndex);
                Value(Section.NumTriangles);
                Value(Section.BaseVertexIndex);
                Value(Section.NumVertices);
                Value(Section.bDisabled);
                Value(Section.BoneMap.Num());
                for (FBoneIndexType Bone : Section.BoneMap) Value(Bone);
                Value(Section.SoftVertices.Num());
                for (const FSoftSkinVertex& Vertex : Section.SoftVertices)
                {
                    Value(Vertex.Position);
                    Value(Vertex.TangentX);
                    Value(Vertex.TangentY);
                    Value(Vertex.TangentZ);
                    Value(Vertex.Color);
                    for (const FVector2f& UV : Vertex.UVs) Value(UV);
                    for (const auto Bone : Vertex.InfluenceBones) Value(Bone);
                    for (const auto Weight : Vertex.InfluenceWeights) Value(Weight);
                }
            }
        }
    }
    Hash.Final();
    uint8 Digest[FSHA1::DigestSize];
    Hash.GetHash(Digest);
    return BytesToHex(Digest, UE_ARRAY_COUNT(Digest));
}

USkeletalMesh* UCarnivalCrowdMaterialEditorLibrary::GenerateSourceFace(UMetaHumanCharacter* Character, FString& OutError)
{
    OutError.Reset();
    if (!Character)
    {
        OutError = TEXT("A source MetaHuman character is required.");
        return nullptr;
    }
    FMetaHumanCharacterGeneratedAssetOptions Options;
    Options.bGenerateBodyMesh = false;
    FMetaHumanCharacterGeneratedAssets Assets;
    if (!UMetaHumanCharacterEditorSubsystem::Get()->TryGenerateCharacterAssets(Character, GetTransientPackage(), Options, Assets)
        || !Assets.FaceMesh)
    {
        OutError = TEXT("Character editor could not generate the temporary source face.");
        return nullptr;
    }
    return Assets.FaceMesh;
}

TArray<UTexture*> UCarnivalCrowdMaterialEditorLibrary::BakeProofMaterialGraph(UTextureGraphInstance* Template,
    const TMap<FName, UMaterialInterface*>& MaterialInputs, const TMap<FName, float>& ScalarInputs,
    const TMap<FName, FName>& OutputNames,
    const FString& OutputFolder, int32 Resolution, FString& OutError)
{
    OutError.Reset();
    TArray<UTexture*> Textures;
    if (!Template || MaterialInputs.IsEmpty() || OutputNames.IsEmpty() || GUsingNullRHI
        || !OutputFolder.StartsWith(TEXT("/Game/Carnival/Crowd/Materials/FaceBakeProof/"))
        || OutputFolder.Contains(TEXT(".."))
        || (Resolution != 256 && Resolution != 512 && Resolution != 1024 && Resolution != 2048))
    {
        OutError = TEXT("Proof bake requires render hardware, a source material and graph, a proof output folder, and a supported resolution.");
        return Textures;
    }
    TStrongObjectPtr<UTextureGraphInstance> Graph(DuplicateObject<UTextureGraphInstance>(Template, GetTransientPackage()));
    Graph->Initialize();
    for (const TPair<FName, UMaterialInterface*>& Input : MaterialInputs)
    {
        FVarArgument* MaterialArg = Graph->InputParams.VarArguments.Find(Input.Key);
        if (!MaterialArg || !Input.Value)
        {
            OutError = FString::Printf(TEXT("Bake graph has no valid material input named %s."), *Input.Key.ToString());
            return Textures;
        }
        FTG_Material MaterialValue;
        MaterialValue.AssetPath = Input.Value->GetPathName();
        MaterialArg->Var.SetAs(MaterialValue);
    }
    for (const TPair<FName, float>& Input : ScalarInputs)
    {
        FVarArgument* Arg = Graph->InputParams.VarArguments.Find(Input.Key);
        if (!Arg)
        {
            OutError = FString::Printf(TEXT("Bake graph has no scalar input named %s."), *Input.Key.ToString());
            return Textures;
        }
        Arg->Var.SetAs(Input.Value);
    }
    TArray<FString> OutputPaths;
    for (TPair<FTG_Id, FTG_OutputSettings>& Pair : Graph->OutputSettingsMap)
    {
        FTG_OutputSettings& Settings = Pair.Value;
        const FName ParamName = Graph->Graph()->GetParamName(FTG_Id(Pair.Key.NodeIdx(), 3));
        const FName* OutputName = OutputNames.Find(ParamName);
        Settings.bShouldExport = OutputName != nullptr;
        if (!OutputName) continue;
        Settings.BaseName = *OutputName;
        const FString Name = Settings.BaseName.ToString();
        if (Name.IsEmpty() || Name == TEXT("None") || Name.Contains(TEXT("/")))
        {
            OutError = TEXT("Bake graph has an invalid output asset name.");
            return Textures;
        }
        Settings.FolderPath = FName(*OutputFolder);
        Settings.Width = static_cast<EResolution>(Resolution);
        Settings.Height = static_cast<EResolution>(Resolution);
        OutputPaths.Add(OutputFolder / Name + TEXT(".") + Name);
    }
    if (OutputPaths.Num() != OutputNames.Num())
    {
        OutError = TEXT("Bake graph has no enabled texture outputs.");
        return Textures;
    }
    TStrongObjectPtr<UTG_AsyncExportTask> Task(UTG_AsyncExportTask::TG_AsyncExportTask(Graph.Get(), true, false, false, true));
    Task->ActivateBlocking(nullptr);
    for (const FString& Path : OutputPaths)
    {
        UTexture* Texture = LoadObject<UTexture>(nullptr, *Path);
        if (!Texture)
        {
            OutError = FString::Printf(TEXT("Bake did not produce %s."), *Path);
            return {};
        }
        Textures.Add(Texture);
    }
    return Textures;
}
