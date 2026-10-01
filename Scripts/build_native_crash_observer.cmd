@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b %errorlevel%
if not exist "F:\Carnival\Saved\Diagnostics" mkdir "F:\Carnival\Saved\Diagnostics"
cl /nologo /std:c++17 /W4 /EHsc /Zi /Od "F:\Carnival\Scripts\NativeCrashObserver.cpp" /Fe:"F:\Carnival\Saved\Diagnostics\NativeCrashObserver.exe" /Fo:"F:\Carnival\Saved\Diagnostics\NativeCrashObserver.obj" /Fd:"F:\Carnival\Saved\Diagnostics\NativeCrashObserver_compile.pdb" /link /DEBUG
