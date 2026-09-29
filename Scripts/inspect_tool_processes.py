"""Read-only process inventory for local Unreal/build tool diagnostics."""
import json
import psutil

names = {"UnrealEditor-Cmd.exe", "dotnet.exe", "python.exe", "pwsh.exe"}
rows = []
for process in psutil.process_iter(["pid", "ppid", "name", "cmdline", "status", "cpu_times"]):
    try:
        command = " ".join(process.info.get("cmdline") or [])
        if process.info["name"] in names and ("Carnival" in command or process.info["name"] == "dotnet.exe"):
            process.info["threads"] = process.num_threads()
            process.info["memory_rss"] = process.memory_info().rss
            rows.append(process.info)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
print(json.dumps(rows, indent=2, default=str))
