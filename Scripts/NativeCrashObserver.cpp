// Local diagnostic launcher: observe only its child, capture unhandled exceptions.
// Uses the installed Windows SDK; does not change system crash settings.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dbghelp.h>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include <iostream>
#pragma comment(lib, "dbghelp.lib")

struct Module { DWORD64 Base; DWORD Size; std::wstring Path; };
static std::wstring Quote(const std::wstring& Arg)
{
    std::wstring Out = L"\""; size_t Slashes = 0;
    for (wchar_t C : Arg)
    {
        if (C == L'\\') { ++Slashes; continue; }
        if (C == L'\"') Out.append(Slashes * 2 + 1, L'\\');
        else Out.append(Slashes, L'\\');
        Slashes = 0; Out += C;
    }
    Out.append(Slashes * 2, L'\\'); return Out + L"\"";
}
static Module ReadModule(HANDLE Process, HANDLE File, void* Base)
{
    Module Result{reinterpret_cast<DWORD64>(Base), 0, L"unknown"};
    wchar_t Path[32768];
    if (File && GetFinalPathNameByHandleW(File, Path, 32768, FILE_NAME_NORMALIZED)) Result.Path = Path;
    IMAGE_DOS_HEADER Dos{}; IMAGE_NT_HEADERS64 Header{}; SIZE_T Read = 0;
    if (ReadProcessMemory(Process, Base, &Dos, sizeof(Dos), &Read) && Dos.e_magic == IMAGE_DOS_SIGNATURE
        && Dos.e_lfanew > 0 && Dos.e_lfanew < 1048576
        && ReadProcessMemory(Process, reinterpret_cast<char*>(Base) + Dos.e_lfanew, &Header, sizeof(Header), &Read)
        && Header.Signature == IMAGE_NT_SIGNATURE) Result.Size = Header.OptionalHeader.SizeOfImage;
    return Result;
}
static void LabelAddress(std::wofstream& Log, DWORD64 Address, const std::map<DWORD64, Module>& Active,
    const std::vector<Module>& Unloaded)
{
    Log << L"0x" << std::hex << Address;
    auto Found = Active.upper_bound(Address);
    if (Found != Active.begin())
    {
        --Found; const auto& M = Found->second;
        if (Address - M.Base < M.Size) { Log << L" " << M.Path << L"+0x" << Address - M.Base; return; }
    }
    for (auto It = Unloaded.rbegin(); It != Unloaded.rend(); ++It)
        if (Address >= It->Base && Address - It->Base < It->Size)
        { Log << L" UNLOADED " << It->Path << L"+0x" << Address - It->Base; return; }
}
static void Capture(HANDLE Process, const DEBUG_EVENT& Event, const std::filesystem::path& Folder,
    const std::map<DWORD64, Module>& Active, const std::vector<Module>& Unloaded)
{
    const auto Stem = L"Unhandled_" + std::to_wstring(Event.dwProcessId) + L"_" + std::to_wstring(GetTickCount64());
    std::wofstream Log(Folder / (Stem + L".txt"));
    auto Record = Event.u.Exception.ExceptionRecord;
    Log << L"process=" << Event.dwProcessId << L" thread=" << Event.dwThreadId << L" code=0x" << std::hex << Record.ExceptionCode << L"\naddress=";
    LabelAddress(Log, reinterpret_cast<DWORD64>(Record.ExceptionAddress), Active, Unloaded); Log << L"\nparameters=";
    for (DWORD I = 0; I < Record.NumberParameters && I < EXCEPTION_MAXIMUM_PARAMETERS; ++I) Log << L" 0x" << Record.ExceptionInformation[I];
    Log << L"\n";
    HANDLE Thread = OpenThread(THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, Event.dwThreadId);
    alignas(16) CONTEXT Context{}; Context.ContextFlags = CONTEXT_FULL;
    const bool GotContext = Thread && GetThreadContext(Thread, &Context);
    if (!GotContext) Log << L"GetThreadContext failed=" << std::dec << GetLastError() << L"\n";
    EXCEPTION_POINTERS Pointers{ &Record, GotContext ? &Context : nullptr };
    MINIDUMP_EXCEPTION_INFORMATION Info{ Event.dwThreadId, &Pointers, FALSE };
    const auto Dump = Folder / (Stem + L".dmp");
    HANDLE File = CreateFileW(Dump.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (File != INVALID_HANDLE_VALUE)
    {
        const bool Written = MiniDumpWriteDump(Process, Event.dwProcessId, File,
            static_cast<MINIDUMP_TYPE>(MiniDumpNormal | MiniDumpWithThreadInfo | MiniDumpWithUnloadedModules),
            GotContext ? &Info : nullptr, nullptr, nullptr);
        Log << L"minidump_written=" << Written << L" error=" << (Written ? 0 : GetLastError()) << L"\n";
        CloseHandle(File);
    }
    else Log << L"Create dump failed=" << GetLastError() << L"\n";
    SymSetOptions(SYMOPT_DEFERRED_LOADS | SYMOPT_UNDNAME | SYMOPT_FAIL_CRITICAL_ERRORS);
    // Empty symbol path avoids adding an external symbol server. Module-local PDBs are sufficient when present.
    if (GotContext && SymInitialize(Process, "", TRUE))
    {
        STACKFRAME64 Frame{}; Frame.AddrPC.Offset = Context.Rip; Frame.AddrPC.Mode = AddrModeFlat;
        Frame.AddrStack.Offset = Context.Rsp; Frame.AddrStack.Mode = AddrModeFlat;
        Frame.AddrFrame.Offset = Context.Rbp; Frame.AddrFrame.Mode = AddrModeFlat;
        Log << L"stack (module offsets remain useful when private symbols are unavailable):\n";
        DWORD64 Previous = 0;
        for (int I = 0; I < 80; ++I)
        {
            if (!StackWalk64(IMAGE_FILE_MACHINE_AMD64, Process, Thread, &Frame, &Context, nullptr,
                SymFunctionTableAccess64, SymGetModuleBase64, nullptr) || !Frame.AddrPC.Offset || Frame.AddrPC.Offset == Previous) break;
            Previous = Frame.AddrPC.Offset; Log << std::dec << I << L" "; LabelAddress(Log, Previous, Active, Unloaded);
            alignas(SYMBOL_INFO) char Buffer[sizeof(SYMBOL_INFO) + MAX_SYM_NAME]{};
            auto* Symbol = reinterpret_cast<SYMBOL_INFO*>(Buffer); Symbol->SizeOfStruct = sizeof(SYMBOL_INFO); Symbol->MaxNameLen = MAX_SYM_NAME;
            DWORD64 Offset = 0;
            if (SymFromAddr(Process, Previous, &Offset, Symbol))
            {
                std::string Name(Symbol->Name, Symbol->NameLen); Log << L" " << std::wstring(Name.begin(), Name.end()) << L"+0x" << std::hex << Offset;
            }
            Log << L"\n";
        }
        SymCleanup(Process);
    }
    if (Thread) CloseHandle(Thread);
    Log << L"\nactive modules:\n";
    for (const auto& Pair : Active) Log << L"0x" << std::hex << Pair.second.Base << L" size=0x" << Pair.second.Size << L" " << Pair.second.Path << L"\n";
    Log << L"\nunloaded modules:\n";
    for (const auto& M : Unloaded) Log << L"0x" << std::hex << M.Base << L" size=0x" << M.Size << L" " << M.Path << L"\n";
    std::wcout << L"Native exception captured: " << Dump << L"\n" << std::flush;
}
int wmain(int Argc, wchar_t** Argv)
{
    if (Argc == 2 && std::wstring(Argv[1]) == L"--native-crash-fixture")
    { volatile int* Target = nullptr; *Target = 42; return 0; }
    if (Argc < 3) { std::wcerr << L"Usage: NativeCrashObserver dump-folder executable [arguments]\n"; return 2; }
    const std::filesystem::path Folder(Argv[1]); std::filesystem::create_directories(Folder);
    std::wstring Command;
    for (int I = 2; I < Argc; ++I) { if (!Command.empty()) Command += L' '; Command += Quote(Argv[I]); }
    STARTUPINFOW Startup{}; Startup.cb = sizeof(Startup); Startup.dwFlags = STARTF_USESTDHANDLES;
    Startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE); Startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE); Startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    PROCESS_INFORMATION Process{};
    if (!CreateProcessW(Argv[2], Command.data(), nullptr, nullptr, TRUE, DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW,
        nullptr, nullptr, &Startup, &Process)) { std::wcerr << L"CreateProcess failed " << GetLastError() << L"\n"; return 3; }
    std::map<DWORD64, Module> Active; std::vector<Module> Unloaded; DWORD Exit = 4;
    for (;;)
    {
        DEBUG_EVENT Event{};
        if (!WaitForDebugEvent(&Event, 1000))
        { if (GetLastError() == ERROR_SEM_TIMEOUT) continue; std::wcerr << L"WaitForDebugEvent failed " << GetLastError() << L"\n"; break; }
        DWORD Status = DBG_CONTINUE;
        if (Event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT)
        {
            auto M = ReadModule(Process.hProcess, Event.u.CreateProcessInfo.hFile, Event.u.CreateProcessInfo.lpBaseOfImage); Active[M.Base] = M;
            if (Event.u.CreateProcessInfo.hFile) CloseHandle(Event.u.CreateProcessInfo.hFile);
        }
        else if (Event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT)
        {
            auto M = ReadModule(Process.hProcess, Event.u.LoadDll.hFile, Event.u.LoadDll.lpBaseOfDll); Active[M.Base] = M;
            if (Event.u.LoadDll.hFile) CloseHandle(Event.u.LoadDll.hFile);
        }
        else if (Event.dwDebugEventCode == UNLOAD_DLL_DEBUG_EVENT)
        {
            const auto Found = Active.find(reinterpret_cast<DWORD64>(Event.u.UnloadDll.lpBaseOfDll));
            if (Found != Active.end()) { Unloaded.push_back(Found->second); Active.erase(Found); }
        }
        else if (Event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT)
        {
            const auto Code = Event.u.Exception.ExceptionRecord.ExceptionCode;
            if (Code != EXCEPTION_BREAKPOINT && Code != EXCEPTION_SINGLE_STEP)
            {
                Status = DBG_EXCEPTION_NOT_HANDLED;
                if (!Event.u.Exception.dwFirstChance) Capture(Process.hProcess, Event, Folder, Active, Unloaded);
            }
        }
        else if (Event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) Exit = Event.u.ExitProcess.dwExitCode;
        if (!ContinueDebugEvent(Event.dwProcessId, Event.dwThreadId, Status))
        { std::wcerr << L"ContinueDebugEvent failed " << GetLastError() << L"\n"; break; }
        if (Event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) break;
    }
    CloseHandle(Process.hThread); CloseHandle(Process.hProcess);
    return static_cast<int>(Exit);
}
