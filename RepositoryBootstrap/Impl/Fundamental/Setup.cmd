@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-04-20 13:43:00
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018-20.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------

echo.

echo ----------------------------------------------------------------------
echo ^|                                                                    ^|
echo ^|             Performing fundamental repository setup                ^|
echo ^|                                                                    ^|
echo ----------------------------------------------------------------------

@REM ----------------------------------------------------------------------
@REM |  Python v2.7.14

REM Python 2.7 will never work on nanoserver, so skip if detected.
if exist C:\License.txt (
    findstr /I /M "/C:CONTAINER OS IMAGE" C:\License.txt >nul
    if "%ERRORLEVEL%" EQU "0" (
        goto :after_27_install
    )
)

echo.
echo ------------------------  Python 2.7.14  -----------------------------

pushd %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\v2.7.14\Windows
call Setup.cmd "%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%"
if %ERRORLEVEL% NEQ 0 exit /B -1

cd "%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%"
echo Installing Python dependencies for 2.7.14...

call :CreateTempScriptName
python -m pip install -r "%~dp0python_requirements.txt" -r "%~dp0python_windows_requirements.txt" 1> "%_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%" 2>&1
set _error=%ERRORLEVEL%
popd

if "%_error%" NEQ "0" (
    echo.
    type %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
    exit /B -1
)
del %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
echo DONE!

:after_27_install

@REM ----------------------------------------------------------------------
@REM |  Python v3.6.5
echo.
echo ------------------------  Python 3.6.5  ------------------------------

pushd %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\v3.6.5\Windows
call Setup.cmd "%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%"
if %ERRORLEVEL% NEQ 0 exit /B -1

cd "%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%"
echo Installing Python dependencies for 3.6.5...

call :CreateTempScriptName
python -m pip install -r "%~dp0python_requirements.txt" -r "%~dp0python_windows_requirements.txt" 1> "%_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%" 2>&1
set _error=%ERRORLEVEL%
popd

if "%_error%" NEQ "0" (
    echo.
    type %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
    exit /B -1
)
del %_SETUP_FUNDAMENTAL_TEMP_SCRIPT_NAME%
echo DONE!

echo.
echo ----------------------------------------------------------------------

REM Invoke fundamental setup activities
%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\v3.6.5\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\python %~dp0\Setup.py %*
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
