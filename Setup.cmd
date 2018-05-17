@REM ----------------------------------------------------------------------
@REM |  
@REM |  Setup.cmd
@REM |  
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2018-04-20 11:21:37
@REM |  
@REM ----------------------------------------------------------------------
@REM |  
@REM |  Copyright David Brownell 2018.
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |  
@REM ----------------------------------------------------------------------
@echo off

@REM ----------------------------------------------------------------------
@REM |  
@REM |  Run as:
@REM |     Setup.cmd [/debug] [/verbose] [/configuration=<config_name>]*
@REM |  
@REM ----------------------------------------------------------------------

REM Begin bootstrap customization
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%~dp0
call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Fundamental\Setup.cmd %*
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
REM End bootstrap customization

if "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%"=="" (
    echo.
    echo ERROR: Please run Activate.cmd within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one.
    echo.
    goto end
)

call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\Impl\Setup.cmd %~dp0 %*

REM Bootstrap customization
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=

:end