// Copyright CarnivalMetaHuman. All Rights Reserved.

#include "CarnivalGame.h"
#include "Modules/ModuleManager.h"
#include "MetaHumanCollection.h"
#include "MetaHumanInstance.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/Package.h"
#include "Serialization/AsyncLoadingEvents.h"
#include "Runtime/Launch/Resources/Version.h"

class FCarnivalGameModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		FDefaultGameModuleImpl::StartupModule();
#if !WITH_EDITORONLY_DATA && ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 8
		// UE 5.8 cooks instance archetype imports to this named default subobject,
		// but creates it only WITH_EDITORONLY_DATA (MetaHumanCollection.cpp).
		// Recreate the same empty template before loading game assets. This leaves
		// the engine installation, source collections and their built data intact.
		auto* Defaults = GetMutableDefault<UMetaHumanCollection>();
		RuntimeCollectionTemplate.Reset(FindObject<UMetaHumanInstance>(Defaults, TEXT("DefaultInstance")));
		if (!RuntimeCollectionTemplate.IsValid())
		{
			RuntimeCollectionTemplate.Reset(NewObject<UMetaHumanInstance>(Defaults, TEXT("DefaultInstance"),
				RF_Public | RF_ArchetypeObject | RF_DefaultSubObject));
			RuntimeCollectionTemplate->SetMetaHumanCollection(Defaults);
			UE_LOG(LogTemp, Display, TEXT("Carnival: restored UE 5.8 MetaHuman collection runtime archetype."));
		}
		// The CDO's original registration completed before this missing child was
		// created. Zen resolves cooked script imports through its registration map,
		// not FindObject; runtime RegistrationComplete only verifies that map.
		// Re-registering the CDO also registers its public nested subobjects.
		NotifyRegistrationEvent(Defaults->GetOutermost()->GetFName(), Defaults->GetFName(),
			ENotifyRegistrationType::NRT_ClassCDO, ENotifyRegistrationPhase::NRP_Finished,
			nullptr, false, Defaults);
#endif
	}
	virtual void ShutdownModule() override
	{
		RuntimeCollectionTemplate.Reset();
		FDefaultGameModuleImpl::ShutdownModule();
	}

private:
	// The engine's corresponding UPROPERTY is editor-only, so retain this
	// archetype explicitly throughout the runtime module's lifetime.
	TStrongObjectPtr<UMetaHumanInstance> RuntimeCollectionTemplate;
};

IMPLEMENT_PRIMARY_GAME_MODULE(FCarnivalGameModule, CarnivalGame, "CarnivalGame");
