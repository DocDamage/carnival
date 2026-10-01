using UnrealBuildTool;

public class CarnivalPopulation : ModuleRules
{
    public CarnivalPopulation(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "MassSpawner",
            "MassAIBehavior",
            "StateTreeModule",
            "MassZoneGraphNavigation",
            "MassNavigation",
            "MassMovement",
            "ZoneGraph"
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "MassActors",
            "MassCommon",
            "MassCore",
            "MassEntity"
        });
    }
}
