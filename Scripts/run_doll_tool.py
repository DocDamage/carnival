"""Run the installed Unreal/Blender tools with explicit argument lists and logs."""
import subprocess
import sys
from pathlib import Path

base = Path(r"F:\Carnival")
logs = base / "Saved/HauntedDollIntegration"
logs.mkdir(parents=True, exist_ok=True)
mode = sys.argv[1]
script = Path(sys.argv[2]) if len(sys.argv) > 2 else None
engine = Path(r"C:\Program Files\UE_5.8\Engine")
if mode == "blender":
    args = [r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe", "--background", "--factory-startup", "--python", str(script)]
elif mode == "unreal":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-run=pythonscript", "-script=" + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "build":
    dotnet = sorted((engine / "Binaries/ThirdParty/DotNet").glob("**/win-x64/dotnet.exe"))[-1]
    args = [str(dotnet), str(engine / "Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll"),
            "CarnivalGameEditor", "Win64", "Development", "-Project=" + str(base / "CarnivalGame.uproject"),
            "-WaitMutex", "-NoHotReloadFromIDE", "-MaxParallelActions=6"]
elif mode == "test":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=Automation RunTests Carnival.HauntedDoll", "-TestExit=Automation Test Queue Empty",
            "-ReportExportPath=" + str(logs / "Automation"), "-abslog=" + str(logs / "Encounter_Test.log")]
elif mode == "render":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-RenderOffscreen", "-nosplash", "-nop4", "-NoSound",
            "-AllowCommandletRendering", "-run=pythonscript", "-script=" + str(script),
            "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "editor":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-RenderOffscreen", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=py " + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "playtest":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=py " + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
else:
    raise ValueError(mode)
log = logs / ((script.stem if script else mode) + "_console.log")
with log.open("w", encoding="utf-8") as output:
    result = subprocess.run(args, cwd=base, stdout=output, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW)
print(mode, "exit", result.returncode, "log", log, flush=True)
print(log.read_text(errors="replace")[-1500:])
sys.exit(result.returncode)
