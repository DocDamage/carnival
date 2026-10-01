#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarnivalCrowdMaterialEditorLibrary.generated.h"

class UMetaHumanCharacter;
class UMetaHumanWardrobeItem;
class UMetaHumanCollection;
class UMetaHumanInstance;
class USkeletalMesh;
class USkeletalMeshComponent;
class UAnimSequence;
class UTextureGraphInstance;
class UMaterialInterface;
class UMaterial;
class UMaterialExpression;
class UTexture;

/** Local material diagnostics and isolated proof bakes; never saves source assets. */
UCLASS()
class CARNIVALPOPULATIONEDITOR_API UCarnivalCrowdMaterialEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Read exact per-input output indices/masks, including repeated links to one source node. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeMaterialExpressionInputs(UMaterialExpression* Expression);
    /** Duplicate the SDK hair master transiently with matching compact mask atlas samplers. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UMaterial* MakeCompactHairSamplerProof(UMaterialInterface* Current, FString& OutError);
    /** Fingerprint loaded geometry, bind pose, skin weights and material mappings for scoped edits. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString GetLoadedMeshStructureDigest(USkeletalMesh* Mesh);

    /** Read loaded LOD sections, original polygon groups and skin weight/bounds diagnostics. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeLoadedMeshSections(USkeletalMesh* Mesh);

    /** Read an assembled component's actual animation, tick policy and posed/reference landmarks. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeSkeletalComponentPose(USkeletalMeshComponent* Component);

    /** Duplicate a baked clip/skeleton transiently and copy matched source body translation modes. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UAnimSequence* MakeAnimationRetargetPolicyProof(UAnimSequence* Baked,
        UAnimSequence* Reference, FString& OutError);

    /** Preserve the source clip's authored reference transforms in a transient named retarget pose. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UAnimSequence* MakeAnimationRetargetReferenceProof(UAnimSequence* Baked,
        UAnimSequence* Reference, bool CopyTranslationModes, FString& OutError);

    /** Convert copied source bone tracks into a transient copy of the candidate skeleton's spaces. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UAnimSequence* MakeAnimationSpaceConversionProof(UAnimSequence* Baked,
        UAnimSequence* Reference, FString& OutError, bool IncludeConstantSourceBones = false);

    /** Compare every mesh bone's component-space position across complete equal-duration clips. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeAnimationPoseAgreement(USkeletalMesh* Mesh, UAnimSequence* Source,
        UAnimSequence* Candidate, int32 Samples, FString& OutError, bool NormalizeUnanimatedSourceBones = false);

    /** Restore missing shared-walk sync markers on the isolated G1 candidate; caller controls saving. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static int32 RestoreCandidateWalkSyncMarkers(UAnimSequence* Source, UAnimSequence* Candidate, FString& OutError);

    /** Read declared slots and their item counts for investigating body surface ownership. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeCollectionSlots(UMetaHumanCollection* Collection);

    /** Read selected wardrobe keys and a fingerprint of authored parameter overrides. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static FString DescribeInstanceSelections(UMetaHumanInstance* Instance);

    /** Rebuild an isolated Dean wardrobe comparison in a fresh owned proof package. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UMetaHumanCollection* BuildBodyOwnershipProof(UMetaHumanCollection* Source, UMetaHumanInstance* SelectionSource,
        const FString& PackageName, bool IncludeCompleteOutfits, FString& OutError);

    /** Select the proof's one shirt, jeans and sneakers on its fresh instance. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static int32 SelectBodyOwnershipProofClothes(UMetaHumanInstance* Instance, FString& OutError);

    /** Rebuild a fresh candidate retaining all items of one clothing composition. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UMetaHumanCollection* BuildClothingFamilyCollection(UMetaHumanCollection* Source,
        const FString& PackageName, bool CompleteOutfitsOnly, bool ConvertBodyAnimations, FString& OutError, int32 BodySourceLOD = -1);

    /** Clone selections and parameter overrides onto a compatible fresh candidate collection. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static UMetaHumanInstance* CloneInstanceForClothingFamily(UMetaHumanInstance* Source,
        UMetaHumanCollection* Collection, const FString& PackageName, FString& OutError);

    /** Build a transient body using the selected source garments' original hidden face maps. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static USkeletalMesh* MakeTrimmedBodyProof(USkeletalMesh* Source,
        const TArray<UMetaHumanWardrobeItem*>& Garments, FString& OutError);

    /** Generate a temporary source face with the character editor's actual skin inputs. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static USkeletalMesh* GenerateSourceFace(UMetaHumanCharacter* Character, FString& OutError);

    /** Export an unsaved copy of a stock bake graph into the isolated proof folder. */
    UFUNCTION(BlueprintCallable, Category="Carnival|Crowd|Materials")
    static TArray<UTexture*> BakeProofMaterialGraph(UTextureGraphInstance* Template,
        const TMap<FName, UMaterialInterface*>& MaterialInputs, const TMap<FName, float>& ScalarInputs,
        const TMap<FName, FName>& OutputNames,
        const FString& OutputFolder, int32 Resolution, FString& OutError);
};
