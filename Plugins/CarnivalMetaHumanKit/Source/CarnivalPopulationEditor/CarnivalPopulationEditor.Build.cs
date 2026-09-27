using UnrealBuildTool;

public class CarnivalPopulationEditor : ModuleRules
{
    public CarnivalPopulationEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "UnrealEd",
            "AssetRegistry",
            "MetaHumanCharacter",
            "MetaHumanCharacterPalette",
            "MetaHumanCrowd",
            "MetaHumanCrowdEditor",
            "MassEntity",
            "MassSpawner",
            "MassRepresentation",
            "MassCrowd",
            "ZoneGraph"
        });
        PrivateDependencyModuleNames.AddRange(new string[] { "Landscape", "Foliage" });
    }
}
