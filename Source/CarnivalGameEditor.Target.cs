// Copyright CarnivalMetaHuman. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class CarnivalGameEditorTarget : TargetRules
{
	public CarnivalGameEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("CarnivalGame");
	}
}
