# ----------------------------------------------------------------------
# |  
# |  Setup.ps1
# |  
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 11:21:37
# |  
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# |  
# |  Run as:
# |     Setup.ps1 [/debug] [/verbose] [/configuration=<config_name>]*
# |  
# ----------------------------------------------------------------------

$env:DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL=1

function ExitScript {
    Remove-Item "NULL" -ErrorAction SilentlyContinue
    exit
}

function echo. {
    echo "`n"
}

# Begin bootstrap customization
$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$PSScriptRoot

$success = Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Fundamental\Setup.cmd $args;`$?"

if( -not $success ){
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

if ([string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL)) {
    Write-Host  ""
    Write-Error "ERROR: Please run Activate.ps1 within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one."
    Write-Host  ""
    
    ExitScript
}

Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Setup.cmd $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL $args"

# Bootstrap customization
Remove-Item "Env:\DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"

ExitScript