@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-05-15 21:47:55
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018-19.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

pushd %~dp0

echo Setting up Python v2.7.14...

if not exist "%1" (
    echo   Unpacking content...

    if exist ".\unzipped" rmdir /S /Q .\unzipped
    powershell.exe -NoP -NonI -Command "Expand-Archive '.\install.zip' '.\unzipped\'"
    
    REM The unzipped dir will not exist if powershell does not exist. However,
    REM that condition doesn't generate an error so we need to determine success
    REM by testing that the expected dir is there or not.
    
    if not exist ".\unzipped" (
        echo.
        echo     Please ensure that PowerShell is available. To do this:
        echo.
        echo        1^) Start Menu -^> "Developer Tools"
        echo        2^) Under "Use developer features", check "Developer mode"
        echo        3^) Under "PowerShell", check:
        echo                Change execution policy to allow local
        echo                PowerShell scripts to run without signing.
        echo                Require signing for remote scripts.
        echo        4^) Click "Apply"
        echo.
        goto :exit
    )

    mkdir "%1"

    pushd .\unzipped
    xcopy /E /Q /Y . "..\%1"
    popd            

    rmdir /S /Q .\unzipped
)

echo DONE!
echo.

:exit
popd
