#include "CarnivalMaterialRepairLibrary.h"
#if WITH_EDITOR
#include "Materials/Material.h"
#include "Materials/MaterialFunction.h"
#include "Materials/MaterialExpression.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionFunctionInput.h"
#include "Materials/MaterialExpressionFunctionOutput.h"
#endif

TArray<FString> UCarnivalMaterialRepairLibrary::RestoreMaterialGraphConnections(UObject* Source, UObject* Destination)
{
    TArray<FString> Errors;
#if WITH_EDITOR
    if (!Source || !Destination || Source == Destination
        || !Destination->GetOutermost()->GetName().StartsWith(TEXT("/Game/Carnival/Crowd/Materials/SamplerRepair/")))
    {
        Errors.Add(TEXT("Destination must be a separate project SamplerRepair material or function."));
        return Errors;
    }
    auto* SourceMaterial = Cast<UMaterial>(Source);
    auto* TargetMaterial = Cast<UMaterial>(Destination);
    auto* SourceFunction = Cast<UMaterialFunction>(Source);
    auto* TargetFunction = Cast<UMaterialFunction>(Destination);
    if ((!SourceMaterial || !TargetMaterial) && (!SourceFunction || !TargetFunction))
    {
        Errors.Add(TEXT("Source and destination must be matching material graph types."));
        return Errors;
    }
    TArray<UMaterialExpression*> SourceExpressions, TargetExpressions;
    if (SourceMaterial)
    {
        for (UMaterialExpression* Expression : SourceMaterial->GetExpressions()) SourceExpressions.Add(Expression);
        for (UMaterialExpression* Expression : TargetMaterial->GetExpressions()) TargetExpressions.Add(Expression);
    }
    else
    {
        for (UMaterialExpression* Expression : SourceFunction->GetExpressions()) SourceExpressions.Add(Expression);
        for (UMaterialExpression* Expression : TargetFunction->GetExpressions()) TargetExpressions.Add(Expression);
    }
    TMap<FName, UMaterialExpression*> ByName;
    for (auto* Expression : TargetExpressions) if (Expression) ByName.Add(Expression->GetFName(), Expression);
    TMap<UMaterialExpression*, UMaterialExpression*> Mapping;
    for (auto* Expression : SourceExpressions)
    {
        if (!Expression) continue;
        auto* const* Match = ByName.Find(Expression->GetFName());
        if (!Match || (*Match)->GetClass() != Expression->GetClass())
            Errors.Add(TEXT("Missing or mismatched duplicate expression: ") + Expression->GetName());
        else Mapping.Add(Expression, *Match);
    }
    if (!Errors.IsEmpty()) return Errors;

    // Rehydrate transient function pin pointers before restoring saved edges.
    // UpdateFromFunctionResource sets IDs from the LOCAL function, preventing
    // the next load/compile from disconnecting them through an ID mismatch.
    for (auto* Expression : TargetExpressions)
        if (auto* Call = Cast<UMaterialExpressionMaterialFunctionCall>(Expression))
            Call->UpdateFromFunctionResource();

    struct FCopy { FExpressionInput* Destination; FExpressionInput Value; };
    TArray<FCopy> Copies;
    auto QueueCopy = [&](FExpressionInput* Original, FExpressionInput* Target, const FString& Label)
    {
        if (!Original || !Target) { Errors.Add(TEXT("Missing input: ") + Label); return; }
        FExpressionInput Value = *Original;
        if (Original->Expression)
        {
            auto* const* Mapped = Mapping.Find(Original->Expression);
            if (!Mapped) { Errors.Add(TEXT("Input references an expression outside its graph: ") + Label); return; }
            Value.Expression = *Mapped;
            const auto& SourceOutputs = Original->Expression->GetOutputs();
            const auto& TargetOutputs = (*Mapped)->GetOutputs();
            if (!SourceOutputs.IsValidIndex(Value.OutputIndex) || !TargetOutputs.IsValidIndex(Value.OutputIndex)
                || SourceOutputs[Value.OutputIndex].OutputName != TargetOutputs[Value.OutputIndex].OutputName)
            {
                Errors.Add(TEXT("Duplicate output index/name differs: ") + Label); return;
            }
        }
        Copies.Add({Target, Value});
    };
    for (const auto& Pair : Mapping)
    {
        auto* Original = Pair.Key;
        auto* Target = Pair.Value;
        for (FExpressionInputIterator It(Original); It; ++It)
        {
            const FName InputName = Original->GetInputName(It.Index);
            FExpressionInput* TargetInput = Target->GetInput(It.Index);
            if (TargetInput && Target->GetInputName(It.Index) != InputName) TargetInput = nullptr;
            // Functions may expose their pins in a different order after refresh.
            if (!TargetInput)
                for (FExpressionInputIterator Candidate(Target); Candidate; ++Candidate)
                    if (Target->GetInputName(Candidate.Index) == InputName) { TargetInput = Candidate.Input; break; }
            QueueCopy(It.Input, TargetInput, Original->GetName() + TEXT(".") + InputName.ToString());
        }
    }
    if (SourceMaterial)
        for (int32 Index = 0; Index < MP_MAX; ++Index)
        {
            const auto Property = static_cast<EMaterialProperty>(Index);
            auto* Input = SourceMaterial->GetExpressionInputForProperty(Property);
            if (Input) QueueCopy(Input, TargetMaterial->GetExpressionInputForProperty(Property), FString::Printf(TEXT("Material property %d"), Index));
        }
    if (!Errors.IsEmpty()) return Errors;
    Destination->Modify();
    for (const FCopy& Copy : Copies) *Copy.Destination = Copy.Value;
    Destination->MarkPackageDirty();
#else
    Errors.Add(TEXT("Material graph repair requires an editor build."));
#endif
    return Errors;
}
