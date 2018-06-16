# ----------------------------------------------------------------------
# |  
# |  Activate.ps1
# |  
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 16:38:31
# |  
# ----------------------------------------------------------------------

function ExitScript {
    if($env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME -and $env:_ACTIVATE_ERROR_LEVEL -eq 0) {
        Remove-Item $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME -ErrorAction SilentlyContinue
    }
    Remove-Item "NULL" -ErrorAction SilentlyContinue

    $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_CLA" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_WORKING_DIR" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_PYTHON_BINARY" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL" -ErrorAction SilentlyContinue
    Remove-Item "Env:\_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME" -ErrorAction SilentlyContinue
    Remove-Item "Env:\PYTHONPATH" -ErrorAction SilentlyContinue
    Remove-Item "Env:\PYTHONUNBUFFERED" -ErrorAction SilentlyContinue
    
    Pop-Location 
    
    exit $env:_ACTIVATE_ERROR_LEVEL
}

function ErrorExit {
    $env:_ACTIVATE_ERROR_LEVEL=-1
    ExitScript
}

function CreateTempScriptName {
    $env:_filename = "$PSScriptRoot\ActivateEnvironment-$(Get-Random -Maximum 99999)-$(Get-Date -Format mm-ss).ps1"
    $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME = $env:_filename
}

function global:echo. {
    echo "`n"
}

Push-Location $PSScriptRoot

$env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
$env:DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL=1
# Read the bootstrap data
if( !(Test-Path "$PSScriptRoot\Generated\Windows\EnvironmentBootstrap.data")) {

    Write-Error `
(@"
 
 
It appears that Setup.cmd has not been run for this repository. Please run Setup.ps1 and run this script again.
 
    [$PSScriptRoot\Windows\EnvironmentBootstrap.data was not found]
 
"@)
    
    ErrorExit
}

Get-Content "$PSScriptRoot\Generated\Windows\EnvironmentBootstrap.data" | ForEach-Object{
    $key, $value = $_.split('=')
    if($key -eq 'fundamental_repo') {
        $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL = (Get-Item $value).FullName
    } elseif ($key -eq 'is_mixin_repo' ){
        $env:_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY = $value
    } elseif ($key -eq 'is_configurable') {
        $env:_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY = $value
    }
}

Get-ChildItem -Path "$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\Tools\Python\v*\Windows" -Filter "python.exe" -Recurse | ForEach-Object {
    $env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY = $_.FullName
}

$env:PYTHONPATH=$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL

# ----------------------------------------------------------------------
# |  List configurations if requested
if ($args[0] -eq "ListConfigurations"){

    # Get the raining args
    $env:_ACTIVATE_ENVIRONMENT_WORKING_DIR=$PSScriptRoot
    $env:_ACTIVATE_ENVIRONMENT_CLA=''

    # There is no shift in powershell, this is how you have to do it.
    $null, $args = $args

    #GetRemainingArgs_ListConfigurations
    $args | ForEach-Object {
        $env:_ACTIVATE_ENVIRONMENT_CLA=$env:_ACTIVATE_ENVIRONMENT_CLA + $_
    }

    Invoke-Expression "$env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY -m RepositoryBootstrap.Impl.Activate ListConfigurations $env:_ACTIVATE_ENVIRONMENT_WORKING_DIR $env:_ACTIVATE_ENVIRONMENT_CLA"
    ExitScript
}

# If here, we are in a verified activation scenario. Set the previous value to this value, knowing that that is the value
# that will be committed.
$env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL

# ----------------------------------------------------------------------
# |  Only allow one activated environment at a time (unless we are activating a mixin repo)
if ($env:_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY -ne "1" -and (![string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY)) -and $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY -ne $PSScriptRoot -and (![string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY))) {
    Write-Error `
(@"
 
 
Only one repository can be activated within an environment at a time, and it appears as if one is already active. Please open a new console and run this script again.
 
    [DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as '{0}']
 
"@ -f $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY)

    ErrorExit
}

# ----------------------------------------------------------------------
# |  A mixin repository can't be activated in isolation
if ($env:_ACTIVATE_ENVIRONMENT_IS_MIXIN_REPOSITORY -eq "1" -and $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG -ne "1") {
    Write-Error `
(@"
 
 
A mixin repository cannot be activated in isolation. Activate another repository before activating this one.
 
"@ -f $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL)

    ErrorExit
}

# ----------------------------------------------------------------------
# |  Prepare the args
if ($env:_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY -ne "0")  {
    if ([string]::IsNullOrEmpty($args[0])) {
        Write-Error `
(@"
 
 
This repository is configurable, which means that it can be activated in a variety of different ways. Please run this script again with a configuration name provided on the command line.
 
"@)

        Invoke-Expression "$env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY -m RepositoryBootstrap.Impl.Activate ListConfigurations $PSScriptRoot"
        
        ErrorExit
    }
    
    if (![string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION)) {
        if ($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION -ne $args[0]) {
            Write-Error `
(@"
 
 
The environment was previously activated with this repository but using a different configuration. Please open a new console window and activate this repository with the new configuration.
 
    [{0} != {1}]
 
"@ -f $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION, $args[0])

            ErrorExit
        }
    }
    
    $env:_ACTIVATE_ENVIRONMENT_CLA = $args
} else {
    $env:_ACTIVATE_ENVIRONMENT_CLA = $args
}

# Create a temporary file that contains output produced by the python script. This lets us quickly bootstrap
# to the python environment while still executing OS-specific commands.
CreateTempScriptName

# Generate...
Invoke-Expression "$env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY -m RepositoryBootstrap.Impl.Activate Activate $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME $PSScriptRoot $env:_ACTIVATE_ENVIRONMENT_CLA"
$env:_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=$LASTEXITCODE

# Invoke...
if (Test-Path $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME) {
    Invoke-Expression "$env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME"
}
$env:_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL = $LASTEXITCODE

# Process errors...
if ($env:_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL -ne "0") {
    Write-Error `
(@"
 
 
Errors were encountered and the environment has not been successfully activated for development.
 
    [{0}\RepositoryBootstrap\Impl\Activate.py failed]
 
"@ -f $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL)

    ErrorExit
}

if ($env:_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL -ne "0" ) {
    Wrie-Error `
(@"
 
 
Errors were encountered and the environment has not been successfully activated for development.

    [{0} failed]
 
"@ -f $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME)

    ErrorExit
}

# Cleanup

Write-Host ""
Write-Host "                    v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^"
Write-Host "                    <                                                                                          >"
Write-Host "                    >   The environment has been activated for this repository and is ready for development.   <"
Write-Host "                    <                                                                                          >"
Write-Host "                    ^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v"
Write-Host ""
Write-Host ""

$env:_ACTIVATE_ERROR_LEVEL=0
ExitScript