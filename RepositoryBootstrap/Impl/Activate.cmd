@REM ----------------------------------------------------------------------
@REM |  
@REM |  Activate.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-05-03 16:38:31
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018-19.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

set _ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%

REM Read the bootstrap data
if not exist "%CD%\Generated\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\EnvironmentBootstrap.data" (
    @echo.
    @echo ERROR: It appears that Setup.cmd has not been run for this repository. Please run Setup.cmd and run this script again.
    @echo.
    @echo        [%CD%\Generated\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\EnvironmentBootstrap.data was not found]
    @echo.

    goto ErrorExit
)

for /f "tokens=1,2 delims==" %%a in (%CD%\Generated\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\EnvironmentBootstrap.data) do (
    if "%%a"=="fundamental_repo" set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%%~fb
    if "%%a"=="is_mixin_repo" set _ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY=%%b
    if "%%a"=="is_configurable" set _ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY=%%b
)

REM Find the python binary
for /f "tokens=*" %%G in ('dir /b /a:d "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\v*"') do (
    if exist "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\%%G\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\python.exe" (
        set _ACTIVATE_ENVIRONMENT_PYTHON_BINARY="%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\Tools\Python\%%G\Windows\%DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME%\python.exe"
    )
)

set PYTHONPATH=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%

@REM ----------------------------------------------------------------------
@REM |  List configurations if requested
if "%1" NEQ "ListConfigurations" goto :AfterListConfigurations
set _ACTIVATE_ENVIRONMENT_CLA=
shift /1

:GetRemainingArgs_ListConfigurations
if "%1" NEQ "" (
    set _ACTIVATE_ENVIRONMENT_CLA=%_ACTIVATE_ENVIRONMENT_CLA% %1
    shift /1
    goto :GetRemainingArgs_ListConfigurations
)

%_ACTIVATE_ENVIRONMENT_PYTHON_BINARY% -m RepositoryBootstrap.Impl.Activate ListConfigurations "%CD%" %_ACTIVATE_ENVIRONMENT_CLA%
goto Exit

:AfterListConfigurations

@REM If here, we are in a verified activation scenario. Set the previous value to this value, knowing that that is the value
@REM that will be committed.
set _ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%

@REM ----------------------------------------------------------------------
@REM |  Only allow one activated environment at a time (unless we are activating a mixin repo)
if "%_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY%" NEQ "1" if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%" NEQ "" if /i "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%" NEQ "%CD%" (
    @echo.
    @echo ERROR: Only one repository can be activated within an environment at a time, and it appears as if one is already active. Please open a new console and run this script again.
    @echo.
    @echo        [DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%"]
    @echo.

    goto :ErrorExit
)

@REM ----------------------------------------------------------------------
@REM |  A mixin repository can't be activated in isolation
if "%_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY%"=="1" if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG%" NEQ "1" (
    @echo.
    @echo ERROR: A mixin repository cannot be activated in isolation. Activate another repository before activating this one.
    @echo.

    goto :ErrorExit
)

@REM ----------------------------------------------------------------------
@REM |  Prepare the args
if "%_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY%" NEQ "0" (
    if "%1" == "" (
        @echo.
        @echo ERROR: This repository is configurable, which means that it can be activated in a variety of different ways. Please run this script again with a configuration name provided on the command line.
        @echo.
        @echo        Available configurations are:
        @echo.
        %_ACTIVATE_ENVIRONMENT_PYTHON_BINARY% -m RepositoryBootstrap.Impl.Activate ListConfigurations "%CD%" command_line
        @echo.
    
        goto :ErrorExit
    )
    
    if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" NEQ "" (
        if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" NEQ "%1" (
            @echo.
            @echo ERROR: The environment was previously activated with this repository but using a different configuration. Please open a new console window and activate this repository with the new configuration.
            @echo.
            @echo        ["%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" != "%1"]
            @echo.
        
            goto :ErrorExit
        )
    )
    
    set _ACTIVATE_ENVIRONMENT_CLA=%*
    goto :AfterClaArgsSet
)

set _ACTIVATE_ENVIRONMENT_CLA=None %*

:AfterClaArgsSet

REM Create a temporary file that contains output produced by the python script. This lets us quickly bootstrap
REM to the python environment while still executing OS-specific commands.
call :CreateTempScriptName

REM Generate...
%_ACTIVATE_ENVIRONMENT_PYTHON_BINARY% -m RepositoryBootstrap.Impl.Activate Activate "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" "%CD%" %_ACTIVATE_ENVIRONMENT_CLA%
set _ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=%ERRORLEVEL%

REM Invoke...
if exist "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" (
    call %_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%
)
set _ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=%ERRORLEVEL%

REM Process errors...
if "%_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL%" NEQ "0" (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully activated for development.
    @echo.
    @echo        [%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Activate.py failed]
    @echo.

    goto :ErrorExit
)

if "%_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL%" NEQ "0" (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully activated for development.
    @echo.
    @echo        [%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME% failed]
    @echo.

    goto :ErrorExit
)

REM Cleanup
del "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%

@echo                                                 ^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^
@echo                                                 ^<                                                                                           ^>
@echo                                                 ^>   The environment has been activated for this repository and is ready for development.    ^<
@echo                                                 ^<                                                                                           ^>
@echo                                                 ^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^
@echo.
@echo.

set _ACTIVATE_ERROR_LEVEL=0
goto Exit

@REM ----------------------------------------------------------------------
:ErrorExit
set _ACTIVATE_ERROR_LEVEL=-1
goto :Exit

@REM ----------------------------------------------------------------------
:Exit
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL%

set _ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=
set _ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=
set _ACTIVATE_ENVIRONMENT_CLA=
set _ACTIVATE_ENVIRONMENT_WORKING_DIR=
set _ACTIVATE_ENVIRONMENT_PYTHON_BINARY=
set _ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY=
set _ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY=
set _ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=
set _ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=
set PYTHONPATH=

exit /B %_ACTIVATE_ERROR_LEVEL%

@REM ---------------------------------------------------------------------------
:CreateTempScriptName
setlocal EnableDelayedExpansion
set _filename=%CD%\Activate-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=%_filename%

if exist "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" goto :CreateTempScriptName
goto :EOF
@REM ---------------------------------------------------------------------------
