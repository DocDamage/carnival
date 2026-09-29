#include "CarnivalHauntedDoll.h"
#include "CarnivalDollAnimInstance.h"
#include "AIController.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NavigationSystem.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

ACarnivalHauntedDoll::ACarnivalHauntedDoll()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(25.f, 71.f);
    GetMesh()->SetRelativeLocation(FVector(0, 0, -71.f));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->SetAnimInstanceClass(UCarnivalDollAnimInstance::StaticClass());
    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
    GetCharacterMovement()->MaxAcceleration = 350.f;
    GetCharacterMovement()->BrakingDecelerationWalking = 450.f;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 180, 0);
    bUseControllerRotationYaw = false;
    AIControllerClass = AAIController::StaticClass();
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
    Tags.Add(TEXT("Carnival.HauntedDoll"));
    ScareAttenuation = CreateDefaultSubobject<USoundAttenuation>(TEXT("ScareAttenuation"));
    ScareAttenuation->Attenuation.bAttenuate = true;
    ScareAttenuation->Attenuation.bSpatialize = true;
    ScareAttenuation->Attenuation.AttenuationShapeExtents = FVector(100.f);
    ScareAttenuation->Attenuation.FalloffDistance = 1000.f;
}

void ACarnivalHauntedDoll::BeginPlay()
{
    Super::BeginPlay();
    if (bMissionControlledInstance) bEncounterEnabled = false;
    if (UWorld* World = GetWorld())
    {
        if (UGameInstance* GameInstance = World->GetGameInstance())
        {
            if (UCarnivalMissionSubsystem* Mission = GameInstance->GetSubsystem<UCarnivalMissionSubsystem>())
            {
                Mission->OnMissionChanged.AddDynamic(this, &ACarnivalHauntedDoll::HandleMissionStateChanged);
            }
        }
    }
    HomeLocation = GetActorLocation();
    HomeRotation = GetActorRotation();
    LastProgressLocation = HomeLocation;
}

void ACarnivalHauntedDoll::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UGameInstance* GameInstance = World->GetGameInstance())
        {
            if (UCarnivalMissionSubsystem* Mission = GameInstance->GetSubsystem<UCarnivalMissionSubsystem>())
            {
                Mission->OnMissionChanged.RemoveDynamic(this, &ACarnivalHauntedDoll::HandleMissionStateChanged);
            }
        }
    }
    Super::EndPlay(EndPlayReason);
}

void ACarnivalHauntedDoll::HandleMissionStateChanged(ECarnivalStoryMissionState NewState, FText)
{
    if (bMissionScareActive && NewState != ECarnivalStoryMissionState::PlayDollScare)
    {
        CancelScriptedMissionScare();
    }
}

void ACarnivalHauntedDoll::CancelScriptedMissionScare()
{
	if (!bMissionScareActive) return;
	if (APlayerController* PlayerController = TargetPlayer ? Cast<APlayerController>(TargetPlayer->GetController()) : nullptr)
	{
		if (PlayerController->PlayerCameraManager)
		{
			PlayerController->PlayerCameraManager->SetManualCameraFade(0.0f, FLinearColor::Black, false);
		}
	}
	bMissionScareActive = false;
    if (ManualAction == MissionHeadSnapAnimation || ManualAction == ScareAnimation)
    {
        ManualAction = nullptr;
        ++AnimationRevision;
    }
    GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TargetPlayer = nullptr;
	SetEncounterState(EDollEncounterState::Idle);
}

void ACarnivalHauntedDoll::ReceiveMissionScareBeat_Implementation(EDollMissionScareBeat Beat, APawn* Player)
{
	APlayerController* PlayerController = Player ? Cast<APlayerController>(Player->GetController()) : nullptr;
	APlayerCameraManager* CameraManager = PlayerController ? PlayerController->PlayerCameraManager : nullptr;
	if (!CameraManager)
	{
		return;
	}

	if (Beat == EDollMissionScareBeat::Blackout)
	{
		const float FadeSeconds = FMath::Clamp(MissionBlackoutSeconds * 0.3f, 0.08f, 0.16f);
		CameraManager->StartCameraFade(0.0f, 1.0f, FadeSeconds, FLinearColor::Black, false, true);
	}
	else if (Beat == EDollMissionScareBeat::Lunge)
	{
		CameraManager->StartCameraFade(1.0f, 0.0f, 0.16f, FLinearColor::Black, false, false);
	}
}

bool ACarnivalHauntedDoll::HasSightTo(const APawn* Player) const
{
    if (!IsValid(Player) || Player == this || !GetWorld()) return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(DollSight), false, this);
    Query.AddIgnoredActor(Player);
    const FVector Eye = GetActorLocation() + FVector(0, 0, 35);
    const FVector Goal = Player->GetActorLocation() + FVector(0, 0, 25);
    return !GetWorld()->LineTraceSingleByChannel(Hit, Eye, Goal, ECC_Visibility, Query);
}

bool ACarnivalHauntedDoll::CanDetectPawn(const APawn* Player) const
{
    if (!bEncounterEnabled || !IsValid(Player) || Player == this) return false;
    const FVector Offset = Player->GetActorLocation() - GetActorLocation();
    if (Offset.SizeSquared() > FMath::Square(DetectionDistance)) return false;
    const float Facing = FVector::DotProduct(GetActorForwardVector(), Offset.GetSafeNormal2D());
    return Facing >= FMath::Cos(FMath::DegreesToRadians(DetectionHalfAngle)) && HasSightTo(Player);
}

bool ACarnivalHauntedDoll::ActivateForPlayer(APawn* Player)
{
    if (EncounterState != EDollEncounterState::Idle || ManualAction || !CanDetectPawn(Player)) return false;
    TargetPlayer = Player;
    SetEncounterState(EDollEncounterState::Notice);
    return true;
}

void ACarnivalHauntedDoll::StopDollMovement()
{
    if (AAIController* AI = Cast<AAIController>(GetController())) AI->StopMovement();
    GetCharacterMovement()->StopMovementImmediately();
}

void ACarnivalHauntedDoll::SetEncounterState(EDollEncounterState State)
{
    if (EncounterState == State) return;
    if (EncounterState == EDollEncounterState::Scare)
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    EncounterState = State;
    StateAge = StuckAge = 0.f;
    if (State == EDollEncounterState::Notice || State == EDollEncounterState::Idle || State == EDollEncounterState::Returning)
        LostSightAge = 0.f;
    MoveRequestAge = 1.f;
    LastProgressLocation = GetActorLocation();
    ++AnimationRevision;
    if (State == EDollEncounterState::Notice || State == EDollEncounterState::Scare ||
        State == EDollEncounterState::Cooldown || State == EDollEncounterState::Idle)
        StopDollMovement();
    if (State == EDollEncounterState::Scare)
    {
        ++ScareCount;
        // Root motion carries the capsule through the authored hop and lunge.
        GetCharacterMovement()->SetMovementMode(MOVE_Flying);
        if (ScareSound) UGameplayStatics::PlaySoundAtLocation(this, ScareSound, GetActorLocation(),
            FRotator::ZeroRotator, ScareVolume, 1.f, 0.f, ScareAttenuation);
        OnScare.Broadcast(TargetPlayer);
    }
    UE_LOG(LogTemp, Display, TEXT("DOLL_STATE %s %s"), *GetName(), *UEnum::GetValueAsString(State));
}

void ACarnivalHauntedDoll::FacePoint(const FVector& Point, float DeltaSeconds)
{
    FRotator Goal = (Point - GetActorLocation()).Rotation();
    Goal.Pitch = Goal.Roll = 0;
    SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), Goal, DeltaSeconds, 150.f));
}

void ACarnivalHauntedDoll::MoveToward(const FVector& Destination, float Speed, float DeltaSeconds)
{
    GetCharacterMovement()->MaxWalkSpeed = Speed;
    MoveRequestAge += DeltaSeconds;
    UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
    FNavLocation Projected;
    const bool bHasNav = Nav && Nav->ProjectPointToNavigation(Destination, Projected, FVector(100, 100, 200));
    if (AAIController* AI = Cast<AAIController>(GetController()); AI && bHasNav)
    {
        if (MoveRequestAge > .35f)
        {
            AI->MoveToLocation(Projected.Location, 35.f, true, true, true, false, nullptr, true);
            MoveRequestAge = 0;
        }
    }
    else
    {
        // A small encounter also works in maps without a built navigation mesh.
        // CharacterMovement still sweeps the capsule, so this cannot pass through walls.
        FacePoint(Destination, DeltaSeconds);
        AddMovementInput((Destination - GetActorLocation()).GetSafeNormal2D());
    }
    if (FVector::DistSquared2D(GetActorLocation(), LastProgressLocation) > 25.f)
    {
        LastProgressLocation = GetActorLocation();
        StuckAge = 0;
    }
    else StuckAge += DeltaSeconds;
}

void ACarnivalHauntedDoll::ResetEncounter()
{
    bMissionScareActive = false;
    if (ManualAction == JumpAnimation && ManualAction)
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    ManualAction = nullptr;
    TargetPlayer = nullptr;
    SetEncounterState(EDollEncounterState::Returning);
}

bool ACarnivalHauntedDoll::PlayDollAction(UAnimSequence* Animation)
{
    if (!Animation || !GetMesh()->GetSkeletalMeshAsset() ||
        Animation->GetSkeleton() != GetMesh()->GetSkeletalMeshAsset()->GetSkeleton()) return false;
    StopDollMovement();
    if (ManualAction && ManualAction == JumpAnimation && Animation != JumpAnimation)
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    ManualAction = Animation;
    if (Animation == JumpAnimation) GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    ActionAge = 0;
    ++AnimationRevision;
    return true;
}

bool ACarnivalHauntedDoll::BeginScriptedMissionScare(APawn* Player)
{
    UWorld* World = GetWorld();
    UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    const UCarnivalMissionSubsystem* Mission = GameInstance ? GameInstance->GetSubsystem<UCarnivalMissionSubsystem>() : nullptr;
    USkeletalMesh* SkeletalMesh = GetMesh()->GetSkeletalMeshAsset();
    if (!Player || bMissionScareActive || !Mission || Mission->GetMissionState() != ECarnivalStoryMissionState::PlayDollScare
        || !SkeletalMesh || !MissionHeadSnapAnimation || !ScareAnimation
        || MissionHeadSnapAnimation->GetSkeleton() != SkeletalMesh->GetSkeleton()
        || ScareAnimation->GetSkeleton() != SkeletalMesh->GetSkeleton())
    {
        return false;
    }

    bEncounterEnabled = false;
    TargetPlayer = Player;
    bMissionScareActive = true;
    MissionScareBeat = EDollMissionScareBeat::HeadSnap;
    MissionScareBeatAge = 0.f;
    SetEncounterState(EDollEncounterState::Notice);
    ++ScareCount;
    if (!PlayDollAction(MissionHeadSnapAnimation))
    {
        bMissionScareActive = false;
        TargetPlayer = nullptr;
        return false;
    }
    ReceiveMissionScareBeat(EDollMissionScareBeat::HeadSnap, Player);
    return true;
}

void ACarnivalHauntedDoll::TickScriptedMissionScare(float DeltaSeconds)
{
    MissionScareBeatAge += DeltaSeconds;
    if (ManualAction)
    {
        ActionAge += DeltaSeconds;
        if (ActionAge < ManualAction->GetPlayLength()) return;
        ManualAction = nullptr;
        ++AnimationRevision;
    }

    switch (MissionScareBeat)
    {
    case EDollMissionScareBeat::HeadSnap:
        MissionScareBeat = EDollMissionScareBeat::Blackout;
        MissionScareBeatAge = 0.f;
        ReceiveMissionScareBeat(EDollMissionScareBeat::Blackout, TargetPlayer);
        break;
    case EDollMissionScareBeat::Blackout:
        if (MissionScareBeatAge < MissionBlackoutSeconds) return;
        MissionScareBeat = EDollMissionScareBeat::Lunge;
        MissionScareBeatAge = 0.f;
        GetCharacterMovement()->SetMovementMode(MOVE_Flying);
        PlayDollAction(ScareAnimation);
        if (ScareSound)
        {
            UGameplayStatics::PlaySoundAtLocation(this, ScareSound, GetActorLocation(),
                FRotator::ZeroRotator, ScareVolume, 1.f, 0.f, ScareAttenuation);
        }
        ReceiveMissionScareBeat(EDollMissionScareBeat::Lunge, TargetPlayer);
        break;
    case EDollMissionScareBeat::Lunge:
        MissionScareBeat = EDollMissionScareBeat::Aftermath;
        MissionScareBeatAge = 0.f;
        GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        ReceiveMissionScareBeat(EDollMissionScareBeat::Aftermath, TargetPlayer);
        break;
    case EDollMissionScareBeat::Aftermath:
        if (MissionScareBeatAge < MissionAftermathSeconds) return;
        if (UWorld* World = GetWorld())
        {
            if (UGameInstance* GameInstance = World->GetGameInstance())
            {
                if (UCarnivalMissionSubsystem* Mission = GameInstance->GetSubsystem<UCarnivalMissionSubsystem>())
                {
                    Mission->ReportDollScareComplete();
                }
            }
        }
        SetEncounterState(EDollEncounterState::Idle);
        TargetPlayer = nullptr;
        bMissionScareActive = false;
        break;
    }
}

void ACarnivalHauntedDoll::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bMissionScareActive)
    {
        TickScriptedMissionScare(DeltaSeconds);
        return;
    }
    if (ManualAction)
    {
        ActionAge += DeltaSeconds;
        if (ActionAge >= ManualAction->GetPlayLength())
        {
            if (ManualAction == JumpAnimation) GetCharacterMovement()->SetMovementMode(MOVE_Falling);
            ManualAction = nullptr;
            ++AnimationRevision;
        }
        return;
    }
    StateAge += DeltaSeconds;
    if (!bEncounterEnabled)
    {
        TargetPlayer = nullptr;
        SetEncounterState(EDollEncounterState::Idle);
        return;
    }
    if (EncounterState == EDollEncounterState::Idle)
    {
        SenseAge += DeltaSeconds;
        if (SenseAge > .15f)
        {
            SenseAge = 0;
            ActivateForPlayer(UGameplayStatics::GetPlayerPawn(this, 0));
        }
        return;
    }
    if (EncounterState == EDollEncounterState::Cooldown)
    {
        if (StateAge >= CooldownSeconds) ResetEncounter();
        return;
    }
    if (EncounterState == EDollEncounterState::Returning)
    {
        if (FVector::Dist2D(GetActorLocation(), HomeLocation) < 40.f)
        {
            SetEncounterState(EDollEncounterState::Idle);
            SetActorRotation(HomeRotation);
        }
        else
        {
            MoveToward(HomeLocation, RunSpeed, DeltaSeconds);
            if (StuckAge > 5.f || StateAge > 30.f)
            {
                // Don't teleport through scenery. Reset the encounter at the safe
                // reached location if the original spot has become inaccessible.
                HomeLocation = GetActorLocation();
                SetEncounterState(EDollEncounterState::Idle);
            }
        }
        return;
    }
    if (EncounterState == EDollEncounterState::Scare)
    {
        if (StateAge >= (ScareAnimation ? ScareAnimation->GetPlayLength() : 2.2f))
            SetEncounterState(EDollEncounterState::Cooldown);
        return;
    }
    if (!IsValid(TargetPlayer) || FVector::Dist2D(GetActorLocation(), HomeLocation) > LeashDistance)
    {
        ResetEncounter();
        return;
    }
    const bool bVisible = HasSightTo(TargetPlayer);
    LostSightAge = bVisible ? 0.f : LostSightAge + DeltaSeconds;
    if (LostSightAge > LoseSightSeconds) { ResetEncounter(); return; }
    if (EncounterState == EDollEncounterState::Notice)
    {
        FacePoint(TargetPlayer->GetActorLocation(), DeltaSeconds);
        if (StateAge >= (NoticeAnimation ? NoticeAnimation->GetPlayLength() : 1.f))
            SetEncounterState(EDollEncounterState::Approach);
        return;
    }
    const FVector Destination = TargetPlayer->GetActorLocation();
    if (bVisible && FVector::Dist2D(GetActorLocation(), Destination) <= ScareDistance &&
        FMath::Abs(GetActorLocation().Z - Destination.Z) < 100.f)
    {
        FacePoint(Destination, 1.f);
        SetEncounterState(EDollEncounterState::Scare);
        return;
    }
    if (EncounterState == EDollEncounterState::Approach && StateAge > ChaseAfterSeconds)
        SetEncounterState(EDollEncounterState::Chase);
    MoveToward(Destination, EncounterState == EDollEncounterState::Chase ? RunSpeed : WalkSpeed, DeltaSeconds);
    if (StuckAge > 4.f) ResetEncounter();
}

UAnimSequence* ACarnivalHauntedDoll::GetDesiredAnimation(bool& bLooping, float& PlayRate) const
{
    PlayRate = 1.f;
    bLooping = false;
    if (ManualAction) return ManualAction;
    if (EncounterState == EDollEncounterState::Scare && ScareAnimation) return ScareAnimation;
    if (EncounterState == EDollEncounterState::Notice && NoticeAnimation) return NoticeAnimation;
    bLooping = true;
    const float Speed = GetVelocity().Size2D();
    if (Speed > 3.f && WalkAnimation)
    {
        const bool bRunning = (EncounterState == EDollEncounterState::Chase || EncounterState == EDollEncounterState::Returning) && RunAnimation;
        PlayRate = FMath::Clamp(Speed / (bRunning ? 101.19048f : 27.21774f), .15f, 2.5f);
        return bRunning ? RunAnimation : WalkAnimation;
    }
    return IdleAnimation;
}
