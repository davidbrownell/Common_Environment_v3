@echo off
REM ----------------------------------------------------------------------
REM |
REM |  Formatter.cmd
REM |
REM |  David Brownell <db@DavidBrownell.com>
REM |      2019-07-02 05:16:16
REM |
REM ----------------------------------------------------------------------
REM |
REM |  Copyright David Brownell 2019
REM |  Distributed under the Boost Software License, Version 1.0. See
REM |  accompanying file LICENSE_1_0.txt or copy at
REM |  http://www.boost.org/LICENSE_1_0.txt.
REM |
REM ----------------------------------------------------------------------
python %~dp0\..\src\Formatter\CommonEnvironment_Formatter\Formatter.py %*
