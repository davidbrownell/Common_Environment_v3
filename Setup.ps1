# ----------------------------------------------------------------------
# |  
# |  Setup.ps1
# |  
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 11:21:37
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright Michael Sharp 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Run as:
# |     Setup.ps1 [/debug] [/verbose] [/configuration=<config_name>]*
# |  
# ----------------------------------------------------------------------

# Begin bootstrap customization
$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$PSScriptRoot
$env:DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL=1
Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Fundamental\Setup.cmd $args" 

function ExitScript {
    Remove-Item "NULL" -ErrorAction SilentlyContinue
    exit
}

if( -not $? ){
    $msg = $Error[0].Exception.Message
    Write-Host  ""
    Write-Host  ""
    Write-Error "ERROR: Errors were encountered and the repository has not been setup for development. Error is $msg."
    Write-Host  ""
    Write-Error "[Fundamental Setup]"
    Write-Host  ""

    ExitScript
}
# End bootstrap customization

if ($env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL -eq "") {
    Write-Host  ""
    Write-Error "ERROR: Please run Activate.ps1 within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one."
    Write-Host  ""
    
    ExitScript
}

Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Setup.cmd $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL $args"

# Bootstrap customization
$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL = ""

ExitScript