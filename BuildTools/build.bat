echo off

if [%FO_ROOT%] == [] (
    set FO_ROOT=%~p0/../
)
if [%FO_WORKSPACE%] == [] (
    set FO_WORKSPACE=Workspace
)
if [%FO_OUTPUT%] == [] (
    set FO_OUTPUT=%FO_WORKSPACE%/output
)

echo Setup environment

CALL :NORMALIZEPATH %FO_ROOT%
set FO_ROOT=%RETVAL%
CALL :NORMALIZEPATH %FO_WORKSPACE%
set FO_WORKSPACE=%RETVAL%
CALL :NORMALIZEPATH %FO_OUTPUT%
set FO_OUTPUT=%RETVAL%

echo FO_ROOT=%FO_ROOT%
echo FO_WORKSPACE=%FO_WORKSPACE%
echo FO_OUTPUT=%FO_OUTPUT%
echo FO_CMAKE_CONTRIBUTION=%FO_CMAKE_CONTRIBUTION%

if [%1] == [win32] (
    set BUILD_ARCH=Win32
) else if [%1] == [win64] (
    set BUILD_ARCH=x64
) else if [%1] == [uwp] (
    set BUILD_ARCH=x64
    set BUILD_CACHE=uwp.cache.cmake
) else if [%1] == [win32-clang] (
    set BUILD_ARCH=Win32
    set BUILD_TOOLSET=ClangCL
) else if [%1] == [win64-clang] (
    set BUILD_ARCH=x64
    set BUILD_TOOLSET=ClangCL
) else (
    echo Invalid build argument
    exit /b 1
)

if [%2] == [client] (
    set BUILD_TARGET=FONLINE_BUILD_CLIENT
) else if [%2] == [server] (
    set BUILD_TARGET=FONLINE_BUILD_SERVER
) else if [%2] == [single] (
    set BUILD_TARGET=FONLINE_BUILD_SINGLE
) else if [%2] == [editor] (
    set BUILD_TARGET=FONLINE_BUILD_EDITOR
) else if [%2] == [mapper] (
    set BUILD_TARGET=FONLINE_BUILD_MAPPER
) else if [%2] == [ascompiler] (
    set BUILD_TARGET=FONLINE_BUILD_ASCOMPILER
) else if [%2] == [baker] (
    set BUILD_TARGET=FONLINE_BUILD_BAKER
) else if [%2] == [toolset] (
    set BUILD_TARGET="FONLINE_BUILD_BAKER=1 -DFONLINE_BUILD_ASCOMPILER"
) else if [%2] == [full] (
    set BUILD_TARGET="FONLINE_BUILD_CLIENT=1 -DFONLINE_BUILD_SERVER=1 -DFONLINE_BUILD_SINGLE=1 -DFONLINE_BUILD_EDITOR=1 -DFONLINE_BUILD_MAPPER=1 -DFONLINE_BUILD_BAKER=1 -DFONLINE_BUILD_ASCOMPILER"
) else (
    echo Invalid build argument
    exit /b 1
)

if [%3] == [] (
    set CONFIG=Release
) else (
    set CONFIG=%3
)

if not exist %FO_WORKSPACE% mkdir %FO_WORKSPACE%
cd %FO_WORKSPACE%

set BUILD_DIR=build-%1-%2-%CONFIG%
if not exist %BUILD_DIR% mkdir %BUILD_DIR%
cd %BUILD_DIR%

if not [%BUILD_TOOLSET%] == [] (
    cmake -A %BUILD_ARCH% -T %BUILD_TOOLSET% -DFONLINE_OUTPUT_PATH="%FO_OUTPUT%" -D%BUILD_TARGET%=1 -DFONLINE_CMAKE_CONTRIBUTION=%FO_CMAKE_CONTRIBUTION% -DFONLINE_UNIT_TESTS=0 "%FO_ROOT%"
) else if [%BUILD_CACHE%] == [] (
    cmake -A %BUILD_ARCH% -DFONLINE_OUTPUT_PATH="%FO_OUTPUT%" -D%BUILD_TARGET%=1 -DFONLINE_CMAKE_CONTRIBUTION=%FO_CMAKE_CONTRIBUTION% -DFONLINE_UNIT_TESTS=0 "%FO_ROOT%"
) else (
    cmake -A %BUILD_ARCH% -C "%FO_ROOT%\BuildTool\%BUILD_CACHE%" -DFONLINE_OUTPUT_PATH="%FO_OUTPUT%" -D%BUILD_TARGET%=1 -DFONLINE_CMAKE_CONTRIBUTION=%FO_CMAKE_CONTRIBUTION% -DFONLINE_UNIT_TESTS=0 "%FO_ROOT%"
)
cmake --build . --config %CONFIG%

exit /B

:NORMALIZEPATH
  set RETVAL=%~f1
  exit /B
