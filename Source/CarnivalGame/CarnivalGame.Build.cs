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
			"EnhancedInput"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"CarnivalPopulation"
		});
	}
}
