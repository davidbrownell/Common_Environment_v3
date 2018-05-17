@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-04-20 13:43:00
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

echo.

echo ----------------------------------------------------------------------
echo ^|                                                                    ^|
echo ^|             Performing fundamental repository setup                ^|
echo ^|                                                                    ^|
echo ----------------------------------------------------------------------

@REM ----------------------------------------------------------------------
@REM |  Python v2.7.14
echo.
echo ------------------------  Python 2.7.14  -----------------------------

call %~dp0\..\..\..\Tools\Python\v2.7.14\Windows\Setup.cmd
set PATH=%~dp0..\..\..\Tools\Python\v2.7.14\Windows;%PATH%

echo Installing Python dependencies for 2.7.14...
call :CreateTempScriptName

python -m pip install -r "%~dp0python_requirements.txt" -r "%~dp0python_windows_requirements.txt" 1> "%_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%" 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo.
    type %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
    exit /B -1
)
del %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
echo DONE!

@REM ----------------------------------------------------------------------
@REM |  Python v3.6.5
echo.
echo ------------------------  Python 3.6.5  ------------------------------

call %~dp0\..\..\..\Tools\Python\v3.6.5\Windows\Setup.cmd
set PATH=%~dp0..\..\..\Tools\Python\v3.6.5\Windows;%PATH%

echo Installing Python dependencies for 3.6.5...
call :CreateTempScriptName

python -m pip install -r "%~dp0python_requirements.txt" -r "%~dp0python_windows_requirements.txt" 1> "%_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%" 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo.
    type %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
    exit /B -1
)
del %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
echo DONE!

REM Use the most recent version of python for the rest of the bootstrap process
echo.
echo ----------------------------------------------------------------------

REM Invoke fundamental setup activities
python %~dp0\Setup.py %*
if "%ERRORLEVEL%" NEQ "0" (
    exit /B -1
)

echo ----------------------------------------------------------------------
echo ----------------------------------------------------------------------
echo ----------------------------------------------------------------------

@REM ----------------------------------------------------------------------
set _SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME=
exit /B 0

@REM ----------------------------------------------------------------------
@REM |  
@REM |  Internal Functions
@REM |  
@REM ----------------------------------------------------------------------
:CreateTempScriptName
setlocal EnableDelayedExpansion
set _filename=%~dp0Setup-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME=%_filename%

if exist "%_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%" goto :CreateTempScriptName
goto :EOF

