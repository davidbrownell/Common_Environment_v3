@REM ----------------------------------------------------------------------
@REM |
@REM |  Deactivate.cmd
@REM |
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2020-04-08 12:44:55
@REM |
@REM ----------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2020
@REM |  Distributed under the Boost Software License, Version 1.0. See
@REM |  accompanying file LICENSE_1_0.txt or copy at
@REM |  http://www.boost.org/LICENSE_1_0.txt.
@REM |
@REM ----------------------------------------------------------------------
@echo off

if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED%"=="" (
    @echo.
    @echo ERROR: It does not appear that this environment has been activated.
    @echo.
    @echo        [DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME was not defined]
    @echo.

    goto ErrorExit
)

REM Create a temporary file that contains output produced by the python script. This lets us quickly bootstrap
REM to the python environment while still executing OS-specific commands.
call :CreateTempScriptName

REM Generate...
python -m RepositoryBootstrap.Impl.Deactivate "%_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" %*
set _DEACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=%ERRORLEVEL%

REM Invoke...
if exist "%_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" (
    call %_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%
)
set _DEACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=%ERRORLEVEL%

REM Process errors...
if "%_DEACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL%" NEQ "0" (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully deactivated.
    @echo.
    @echo        [%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Deactivate.py failed]
    @echo.

    goto :ErrorExit
)

if "%_DEACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL%" NEQ "0" (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully deactivated.
    @echo.
    @echo        [%_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME% failed]
    @echo.

    goto :ErrorExit
)

REM Cleanup
del "%_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%"

@echo                                                                        ^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^
@echo                                                                        ^<                                             ^>
@echo                                                                        ^>    The environment has been deactivated.    ^<
@echo                                                                        ^<                                             ^>
@echo                                                                        ^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^
@echo.
@echo.

goto Exit

@REM ----------------------------------------------------------------------
:ErrorExit
set _DEACTIVATE_ERROR_LEVEL=-1
goto :Exit

@REM ----------------------------------------------------------------------
:Exit

set _DEACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=
set _DEACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=
set _DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=

exit /B %_DEACTIVATE_ERROR_LEVEL%

@REM ---------------------------------------------------------------------------
:CreateTempScriptName
setlocal EnableDelayedExpansion
set _filename=%CD%\Deactivate-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=%_filename%

if exist "%_DEACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" goto :CreateTempScriptName
goto :EOF
@REM ---------------------------------------------------------------------------
