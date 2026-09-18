#pragma once

#include "Modules/ModuleManager.h"

class FCarnivalPopulationModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
