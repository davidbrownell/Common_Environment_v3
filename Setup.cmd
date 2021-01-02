@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-04-20 11:21:37
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018-21.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

@REM ----------------------------------------------------------------------
@REM |  
@REM |  Run as:
@REM |     Setup.cmd [/debug] [/verbose] ["/name=<name>"] ["/configuration=<config_name>"]*
@REM |  
@REM ----------------------------------------------------------------------

@REM Begin bootstrap customization
pushd "%~dp0"

set _PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%~dp0

set _SETUP_ERROR=0

@REM Only run the fundamental setup if we are in a standard setup scenario
set _SETUP_FIRST_ARG=%~1

if "%_SETUP_FIRST_ARG%" NEQ "" (
    if "%_SETUP_FIRST_ARG:~,1%" NEQ "/" (
        if "%_SETUP_FIRST_ARG:~,1%" NEQ "-" (
            goto :AfterFundamentalSetup
        )
    )
)

@REM Get the tools unique name

@REM This should match the value in RepositoryBootstrap/Constants.py:DEFAULT_ENVIRONMENT_NAME
set _ENVIRONMENT_NAME=DefaultEnv
set _SETUP_CLA=

@REM Note that the following loop has been crafted to work around batch's crazy
@REM expansion rules. Modify at your own risk!
:GetRemainingArgs_Begin

if "%~1"=="" goto :GetRemainingArgs_End

set _ARG=%~1

if "%_ARG:~,6%"=="/name=" goto :GetRemainingArgs_Name1
if "%_ARG:~,6%"=="-name=" goto :GetRemainingArgs_Name1

if "%_ARG:~,9%"=="/name_EQ_" goto :GetRemainingArgs_Name2
if "%_ARG:~,9%"=="-name_EQ_" goto :GetRemainingArgs_Name2

@REM If here, we are looking at an arg that should be passed to the script
set _SETUP_CLA=%_SETUP_CLA% "%_ARG%"
goto :GetRemainingArgs_Continue

:GetRemainingArgs_Name1
@REM If here, we are looking at a name argument
set _ENVIRONMENT_NAME=%_ARG:~6%
goto :GetRemainingArgs_Continue

:GetRemainingArgs_Name2
@REM If here, we are looking at a name argument
set _ENVIRONMENT_NAME=%_ARG:~9%
goto :GetRemainingArgs_Continue

:GetRemainingArgs_Continue
shift /1
goto :GetRemainingArgs_Begin

:GetRemainingArgs_End

@REM This should match the value in RepositoryBootstrap/Constants.py:DE_ENVIRONMENT_NAME
set DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME=%_ENVIRONMENT_NAME%

call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Fundamental\Setup.cmd %_SETUP_CLA%
if %ERRORLEVEL% NEQ 0 (
    @echo.
    @echo.
    @echo.
    @echo ERROR: Errors were encountered and the repository has not been setup for development.
    @echo.
    @echo        [Fundamental Setup]
    @echo.

    goto end
)

:AfterFundamentalSetup
REM End bootstrap customization

if "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%"=="" (
    echo.
    echo ERROR: Please run Activate.cmd within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one.
    echo.
    goto end
)

call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Setup.cmd %_SETUP_CLA%
set _SETUP_ERROR=%ERRORLEVEL%

REM Bootstrap customization
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%_PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%

:end
set _ARG=
set _SETUP_CLA=
set _ENVIRONMENT_NAME=
set _SETUP_FIRST_ARG=
set _PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=

popd

if %_SETUP_ERROR% NEQ 0 (exit /B %_SETUP_ERROR%)
