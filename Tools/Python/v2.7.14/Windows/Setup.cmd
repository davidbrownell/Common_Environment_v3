@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-05-15 21:47:55
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

pushd %~dp0

echo Setting up Python v2.7.14...

if not exist "./python.exe" (
    echo   Unpacking content...

    if exist ".\unzipped" rmdir /S /Q .\unzipped
    powershell.exe -NoP -NonI -Command "Expand-Archive '.\install.zip' '.\unzipped\'"

    pushd .\unzipped
    xcopy /E /Q /Y . ..
    popd            

    rmdir /S /Q .\unzipped
)

echo DONE!
echo.

popd
