#include "CarnivalBalloonFlightComponent.h"

#include "CarnivalRideOperationComponent.h"
#include "CarnivalRidePassengerComponent.h"
#include "CarnivalRideSeatComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TimelineComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#if WITH_EDITOR
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "Kismet/KismetMathLibrary.h"
#endif

int32 UCarnivalBalloonFlightComponent::RepairRedundantFireAutoActivation(UBlueprint* Blueprint)
{
#if WITH_EDITOR
    if (!Blueprint || !Blueprint->GetPathName().StartsWith(TEXT("/Game/Carnival/Rides/Adapted/"))) return -1;
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs)
    {
        if (!Graph || Graph->GetFName() != TEXT("FireSetup")) continue;
        UEdGraphNode* Candidate = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            if (Node && Node->FindPin(TEXT("bNewAutoActivate")))
            {
                if (Candidate) return -1;
                Candidate = Node;
            }
        }
        if (!Candidate) return 0;
        UEdGraphPin* Input = Candidate->FindPin(TEXT("execute"));
        UEdGraphPin* Output = Candidate->FindPin(TEXT("then"));
        UEdGraphPin* Targets = Candidate->FindPin(TEXT("self"));
        UEdGraphPin* Enabled = Candidate->FindPin(TEXT("bNewAutoActivate"));
        if (!Input || !Output || !Targets || Input->LinkedTo.Num()!=1 || Output->LinkedTo.Num()!=1
            || Targets->LinkedTo.Num()!=2 || Enabled->LinkedTo.Num()!=1) return -1;
        TSet<FName> TargetNames;
        for (UEdGraphPin* Target : Targets->LinkedTo) TargetNames.Add(Target->PinName);
        if (!TargetNames.Contains(TEXT("Fire")) || !TargetNames.Contains(TEXT("Fire1"))) return -1;
        UEdGraphNode* Branch = Output->LinkedTo[0]->GetOwningNode();
        UEdGraphPin* Condition = Branch ? Branch->FindPin(TEXT("Condition")) : nullptr;
        UEdGraphPin* Active = Branch ? Branch->FindPin(TEXT("then")) : nullptr;
        UEdGraphPin* Inactive = Branch ? Branch->FindPin(TEXT("else")) : nullptr;
        if (!Condition || Condition->LinkedTo.Num()!=1 || Condition->LinkedTo[0]!=Enabled->LinkedTo[0]
            || !Active || !Inactive || Active->LinkedTo.Num()!=1 || Inactive->LinkedTo.Num()!=1
            || !Active->LinkedTo[0]->GetOwningNode()->GetNodeTitle(ENodeTitleType::FullTitle).ToString().StartsWith(TEXT("Activate"))
            || !Inactive->LinkedTo[0]->GetOwningNode()->GetNodeTitle(ENodeTitleType::FullTitle).ToString().StartsWith(TEXT("Deactivate"))) return -1;
        // The same boolean already drives the correct runtime Activate/Deactivate
        // branch. Only the redundant construction-only setting is removed.
        Blueprint->Modify(); Graph->Modify(); Candidate->Modify(); Branch->Modify();
        UEdGraphPin* Previous = Input->LinkedTo[0];
        UEdGraphPin* Next = Output->LinkedTo[0];
        Previous->MakeLinkTo(Next);
        FBlueprintEditorUtils::RemoveNode(Blueprint, Candidate, true);
        FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
        return 1;
    }
#endif
    return -1;
}

int32 UCarnivalBalloonFlightComponent::RepairEmptyAnnouncementQueue(UBlueprint* Blueprint)
{
#if WITH_EDITOR
    if (!Blueprint || Blueprint->GetPathName() != TEXT("/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/BP_Rides_Parent.BP_Rides_Parent")) return -1;
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs)
    {
        if (!Graph || Graph->GetFName() != TEXT("Animation")) continue;
        auto Find = [&](FName Name) -> UEdGraphNode*
        {
            for (UEdGraphNode* Node : Graph->Nodes) if (Node && Node->GetFName() == Name) return Node;
            return nullptr;
        };
        auto Pin = [&](FName Name, FName PinName) -> UEdGraphPin*
        {
            auto* Node = Find(Name); return Node ? Node->FindPin(PinName) : nullptr;
        };
        auto* Previous = Pin(TEXT("K2Node_ExecutionSequence_13"), TEXT("then_1"));
        auto* Selection = Pin(TEXT("K2Node_VariableSet_25"), TEXT("execute"));
        auto* Reset = Pin(TEXT("K2Node_VariableSet_27"), TEXT("execute"));
        auto* Length = Pin(TEXT("K2Node_CallArrayFunction_11"), TEXT("ReturnValue"));
        auto* Array = Pin(TEXT("K2Node_CallArrayFunction_11"), TEXT("TargetArray"));
        if (!Previous || !Selection || !Reset || !Length || !Array || Array->LinkedTo.Num() != 1
            || Array->LinkedTo[0]->PinName != TEXT("announcementsToPlay_temp") || Length->PinType.PinCategory != TEXT("int")) return -1;
        auto* Existing = Cast<UK2Node_IfThenElse>(Find(TEXT("Carnival_AnnouncementQueueReady")));
        if (Existing)
        {
            auto* Compare = Cast<UK2Node_CallFunction>(Find(TEXT("Carnival_AnnouncementQueueNotEmpty")));
            auto* A = Compare ? Compare->FindPin(TEXT("A")) : nullptr;
            auto* B = Compare ? Compare->FindPin(TEXT("B")) : nullptr;
            return Compare && Compare->GetTargetFunction()
                && Compare->GetTargetFunction()->GetFName() == TEXT("Greater_IntInt")
                && A && A->LinkedTo.Num() == 1 && A->LinkedTo[0] == Length
                && B && B->LinkedTo.IsEmpty() && B->DefaultValue == TEXT("0")
                && Previous->LinkedTo.Num() == 1 && Previous->LinkedTo[0] == Existing->GetExecPin()
                && Existing->GetThenPin()->LinkedTo.Contains(Selection)
                && Existing->GetElsePin()->LinkedTo.Contains(Reset)
                && Existing->GetConditionPin()->LinkedTo.Contains(Compare->GetReturnValuePin()) ? 0 : -1;
        }
        if (Find(TEXT("Carnival_AnnouncementQueueNotEmpty")) || Previous->LinkedTo.Num() != 1
            || Previous->LinkedTo[0] != Selection || Selection->LinkedTo.Num() != 1) return -1;
        auto* GreaterFunction = UKismetMathLibrary::StaticClass()->FindFunctionByName(TEXT("Greater_IntInt"));
        if (!GreaterFunction) return -1;
        Blueprint->Modify(); Graph->Modify(); Previous->GetOwningNode()->Modify(); Selection->GetOwningNode()->Modify(); Reset->GetOwningNode()->Modify();
        auto* Compare = NewObject<UK2Node_CallFunction>(Graph, TEXT("Carnival_AnnouncementQueueNotEmpty"), RF_Transactional);
        Graph->AddNode(Compare, false, false); Compare->CreateNewGuid(); Compare->SetFromFunction(GreaterFunction); Compare->AllocateDefaultPins();
        auto* Guard = NewObject<UK2Node_IfThenElse>(Graph, TEXT("Carnival_AnnouncementQueueReady"), RF_Transactional);
        Graph->AddNode(Guard, false, false); Guard->CreateNewGuid(); Guard->AllocateDefaultPins();
        Guard->NodeComment = TEXT("Only select/play/remove after refill leaves at least one announcement. Empty rides reset their timer.");
        Guard->NodePosX = Selection->GetOwningNode()->NodePosX - 280;
        Guard->NodePosY = Selection->GetOwningNode()->NodePosY;
        Compare->NodePosX = Guard->NodePosX - 240; Compare->NodePosY = Guard->NodePosY + 160;
        Compare->FindPinChecked(TEXT("B"))->DefaultValue = TEXT("0");
        Length->MakeLinkTo(Compare->FindPinChecked(TEXT("A")));
        Compare->GetReturnValuePin()->MakeLinkTo(Guard->GetConditionPin());
        Previous->BreakLinkTo(Selection); Previous->MakeLinkTo(Guard->GetExecPin());
        Guard->GetThenPin()->MakeLinkTo(Selection); Guard->GetElsePin()->MakeLinkTo(Reset);
        FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
        return 1;
    }
#endif
    return -1;
}

TArray<FString> UCarnivalBalloonFlightComponent::DescribeBlueprintExecution(UBlueprint* Blueprint)
{
    TArray<FString> Result;
#if WITH_EDITOR
    if (!Blueprint) return Result;
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    for (const UEdGraph* Graph : Graphs) for (const UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node) continue;
        Result.Add(FString::Printf(TEXT("%s/%s [%s] %s"), *Graph->GetName(), *Node->GetName(),
            *Node->GetClass()->GetName(), *Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString()));
        for (const UEdGraphPin* Pin : Node->Pins)
        {
            if (!Pin) continue;
            FString Links;
            for (const UEdGraphPin* Other : Pin->LinkedTo)
                if (Other && Other->GetOwningNode()) Links += Other->GetOwningNode()->GetName() + TEXT(".") + Other->PinName.ToString() + TEXT(" ");
            Result.Add(FString::Printf(TEXT("  %s %s [%s] default=%s links=%s"),
                Pin->Direction == EGPD_Input ? TEXT("in") : TEXT("out"), *Pin->PinName.ToString(),
                *Pin->PinType.PinCategory.ToString(), *Pin->DefaultValue, *Links));
        }
    }
#endif
    return Result;
}

UCarnivalBalloonFlightComponent::UCarnivalBalloonFlightComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UCarnivalBalloonFlightComponent::BeginPlay()
{
    Super::BeginPlay();
    ResolveComponents();
}

bool UCarnivalBalloonFlightComponent::ResolveComponents()
{
    if (!IsValid(GetOwner())) return false;
    if (!IsValid(Operation))
    {
        Operation = GetOwner()->FindComponentByClass<UCarnivalRideOperationComponent>();
        if (Operation) AddTickPrerequisiteComponent(Operation);
    }
    if (!IsValid(MotionSource))
    {
        TArray<UStaticMeshComponent*> Meshes;
        GetOwner()->GetComponents<UStaticMeshComponent>(Meshes);
        for (auto* Mesh : Meshes)
            if (Mesh->GetFName() == MotionComponentName) { MotionSource = Mesh; break; }
    }
    ConfigurationError = !Operation ? TEXT("Balloon requires an attended ride operation")
        : !MotionSource || !MotionSource->GetStaticMesh() ? TEXT("Balloon motion mesh is missing") : TEXT("");
    return ConfigurationError.IsEmpty();
}

void UCarnivalBalloonFlightComponent::StopVendorMotion() const
{
    TArray<UTimelineComponent*> Timelines;
    GetOwner()->GetComponents<UTimelineComponent>(Timelines);
    for (auto* Timeline : Timelines)
        if (Timeline->GetFName() == VendorMotionTimelineName) Timeline->Stop();
}

bool UCarnivalBalloonFlightComponent::IsFlightStepClear(const FTransform& Target)
{
    const FBox Bounds = MotionSource->GetStaticMesh()->GetBoundingBox();
    const float Split = FMath::Clamp(CanopyStartZ, static_cast<float>(Bounds.Min.Z + 1), static_cast<float>(Bounds.Max.Z - 1));
    const FBox Sections[] = {
        FBox(FVector(-BasketHalfWidth, -BasketHalfWidth, Bounds.Min.Z), FVector(BasketHalfWidth, BasketHalfWidth, Split)),
        FBox(FVector(Bounds.Min.X, Bounds.Min.Y, Split), Bounds.Max)
    };
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_WorldStatic);
    Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    Objects.AddObjectTypesToQuery(ECC_PhysicsBody);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarnivalBalloonFlight), false, GetOwner());
    // Staff and riding characters are Pawns, and are deliberately not blockers.
    const FTransform Current = MotionSource->GetComponentTransform();
    for (const FBox& Section : Sections)
    {
        FHitResult Hit;
        if (GetWorld()->SweepSingleByObjectType(Hit, Current.TransformPosition(Section.GetCenter()),
            Target.TransformPosition(Section.GetCenter()), Target.GetRotation(), Objects,
            FCollisionShape::MakeBox(Section.GetExtent() * Target.GetScale3D().GetAbs()), Params))
        {
            LastObstruction = FString::Printf(TEXT("%s / %s at %s (initial overlap=%d)"),
                *GetPathNameSafe(Hit.GetActor()), *GetPathNameSafe(Hit.GetComponent()),
                *Hit.ImpactPoint.ToString(), Hit.bStartPenetrating);
            return false;
        }
    }
    return true;
}

void UCarnivalBalloonFlightComponent::RequestControlledReturn()
{
    TArray<UCarnivalRideSeatComponent*> Seats;
    GetOwner()->GetComponents<UCarnivalRideSeatComponent>(Seats);
    for (auto* Seat : Seats)
        if (AActor* Passenger = Seat->GetOccupant())
            if (Operation->RequestPassengerExit(Passenger)) return;
    if (IsValid(Operation->PlayerOperator)) Operation->OperatorStop(Operation->PlayerOperator);
    // An unattended empty cycle may simply hold until its normal deadline.
}

void UCarnivalBalloonFlightComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!ResolveComponents()) return;
    // The vendor timeline is decorative drifting motion. It must not compete
    // with the ground station flight or with the operation's home interpolation.
    StopVendorMotion();
    if (!Operation->IsReady()) return;
    if (!bHasLoadingPose && (Operation->State == ECarnivalOperationState::Loading || Operation->State == ECarnivalOperationState::Closed
        || Operation->State == ECarnivalOperationState::Securing))
    {
        LoadingPose = MotionSource->GetRelativeTransform();
        bHasLoadingPose = true;
    }
    const bool bRunning = Operation->State == ECarnivalOperationState::Running;
    if (!bRunning)
    {
        bWasRunning = false;
        if (Operation->State == ECarnivalOperationState::Loading) CurrentLift = 0.f;
        return; // Returning belongs exclusively to UCarnivalRideOperationComponent.
    }
    if (!bHasLoadingPose) return;
    if (!bWasRunning)
    {
        FlightSeconds = 0.f;
        bLastCycleObstructed = false;
        LastObstruction.Reset();
        bWasRunning = true;
    }
    if (bLastCycleObstructed) return;
    FlightSeconds += FMath::Max(DeltaTime, 0.f);
    const float Progress = FMath::Clamp(FlightSeconds / FMath::Max(Operation->CycleSeconds, 1.f), 0.f, 1.f);
    const float LiftFraction = Progress < .3f ? FMath::SmoothStep(0.f, .3f, Progress)
        : Progress > .7f ? 1.f - FMath::SmoothStep(.7f, 1.f, Progress) : 1.f;
    const float Lift = FMath::Clamp(FlightHeight, 100.f, 3000.f) * LiftFraction;
    FTransform Relative = LoadingPose;
    Relative.AddToTranslation(FVector(0, 0, Lift));
    const USceneComponent* Parent = MotionSource->GetAttachParent();
    const FTransform Target = Parent ? Relative * Parent->GetComponentTransform() : Relative;
    if (!IsFlightStepClear(Target))
    {
        bLastCycleObstructed = true;
        RequestControlledReturn();
        return;
    }
    MotionSource->SetRelativeTransform(Relative);
    CurrentLift = Lift;
}
