// Copyright CarnivalMetaHuman. All Rights Reserved.

using UnrealBuildTool;

public class CarnivalGame : ModuleRules
{
	public CarnivalGame(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"UMG",
			"Niagara",
			"AIModule",
			"NavigationSystem"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
            "CarnivalPopulation",
            "MetaHumanCharacterPalette",
            "MetaHumanCrowd"
        });

        if (Target.bBuildEditor)
            PrivateDependencyModuleNames.Add("UnrealEd");
	}
}
