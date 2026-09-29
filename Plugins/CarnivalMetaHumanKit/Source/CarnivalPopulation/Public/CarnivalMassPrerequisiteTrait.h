#pragma once

#include "MassEntityTraitBase.h"
#include "CarnivalMassPrerequisiteTrait.generated.h"

/** Supplies core Mass fragments required by the MetaHuman Crowd visualization trait. */
UCLASS()
class CARNIVALPOPULATION_API UCarnivalMassPrerequisiteTrait : public UMassEntityTraitBase
{
	GENERATED_BODY()

public:
	virtual void BuildTemplate(FMassEntityTemplateBuildContext& BuildContext, const UWorld& World) const override;
};
