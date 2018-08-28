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

# Begin bootstrap customization
$env:_PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$PSScriptRoot

# Only run the fundamental setup if we are in a standard setup scenario
if ( ([string]::IsNullOrEmpty($args[0])) -or $args[0].Substring(0,1) -eq "/" -or $args[0].Substring(0,1) -eq "-" ) {
    $success = Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Fundamental\Setup.cmd $args;`$?"

    if( -not $success ){
        $msg = $Error[0].Exception.Message

        Write-Error (@"
 
 
Errors were encountered and the repository has not been setup for development.
 
    [Fundamental Setup: {0}]
 
"@ -f $msg)

        ExitScript
    }
}
# End bootstrap customization

if ([string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL)) {
    Write-Error @"
 
 
Please run Activate.ps1 within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one.
 
"@

    ExitScript
}

Invoke-Expression "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Setup.cmd $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL $args"

# Bootstrap customization
$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$env:_PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
$env:_PREV_DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL = ''

ExitScript