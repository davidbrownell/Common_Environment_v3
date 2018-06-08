# ----------------------------------------------------------------------
# |  
# |  Activate.ps1
# |  
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 16:38:31
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright Michael Sharp 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------

function ExitScript {
    if($env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME){
        Remove-Item $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME -ErrorAction SilentlyContinue
    }
    Remove-Item "NULL" -ErrorAction SilentlyContinue

    $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL
    $env:_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=''
    $env:_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=''
    $env:_ACTIVATE_ENVIRONMENT_CLA=''
    $env:_ACTIVATE_ENVIRONMENT_WORKING_DIR=''
    $env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY=''
    $env:_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY=''
    $env:_ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY=''
    $env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=''
    $env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=''
    $env:PYTHONPATH=''
    $env:PYTHONUNBUFFERED=''
    
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

Push-Location $PSScriptRoot

$env:_ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
$env:DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL=1
# Read the bootstrap data
if( !(Test-Path "$PSScriptRoot\Generated\Windows\EnvironmentBootstrap.data")) {
    Write-Host  ""
    Write-Error "It appears that Setup.cmd has not been run for this repository. Please run Setup.ps1 and run this script again."
    Write-Host  ""
    Write-Error "[$PSScriptRoot\Windows\EnvironmentBootstrap.data was not found]"
    Write-Host  ""

    ErrorExit
}

Get-Content "$PSScriptRoot\Generated\Windows\EnvironmentBootstrap.data" | ForEach-Object{
    $key, $value = $_.split('=')
    if($key -eq 'fundamental_repo') {
        $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL = (Get-Item $value).FullName
    } elseif ($key -eq 'is_tool_repo' ){
        $env:_ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY = $value
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
# |  Only allow one activated environment at a time (unless we are activating a tool repo)
if ($env:_ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY -ne "1" -and $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY -ne "" -and $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY -ne $PSScriptRoot -and $null -ne $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY) {
    Write-Host  ""
    Write-Error "Only one repository can be activated within an environment at a time, and it appears as if one is already active. Please open a new console and run this script again."
    Write-Host  ""
    Write-Error "[DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as '$env:DEVELOPMENT_ENVIRONMENT_REPOSITORY']"
    Write-Host  ""

    ErrorExit
}

# ----------------------------------------------------------------------
# |  A tool repository can't be activated in isolation
if ($env:_ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY -eq "1" -and $env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG -ne "1") {
    Write-Host  ""
    Write-Error "A tool repository cannot be activated in isolation. Activate another repository before activating this one."
    Write-Host  ""

    ErrorExit
}

# ----------------------------------------------------------------------
# |  Prepare the args
if ($env:_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY -ne "0")  {
    if ($args[0] -eq "") {
        Write-Host  ""
        Write-Error "This repository is configurable, which means that it can be activated in a variety of different ways. Please run this script again with a configuration name provided on the command line."
        Write-Host  ""
        Write-Error "Available configurations are:"
        Write-Host  ""
        Invoke-Expression "$env:_ACTIVATE_ENVIRONMENT_PYTHON_BINARY -m RepositoryBootstrap.Impl.Activate ListConfigurations $PSScriptRoot command_line"
        Write-Host  ""
    
        ErrorExit
    }
    
    if (![string]::IsNullOrEmpty($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION)) {
        if ($env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION -ne $args[0]) {
            Write-Host  ""
            Write-Error "The environment was previously activated with this repository but using a different configuration. Please open a new console window and activate this repository with the new configuration."
            Write-Host  ""
            Write-Error "[$env:DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION != $args[0]]"
            Write-Host  ""
        
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
    Write-Host  ""
    Write-Error "Errors were encountered and the environment has not been successfully activated for development."
    Write-Host  ""
    Write-Error "[$env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\Impl\Activate.py failed]"
    Write-Host  ""

    ErrorExit
}

if ($env:_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL -ne "0" ){
    Write-Debug ""
    Write-Error "Errors were encountered and the environment has not been successfully activated for development."
    Write-Host  ""
    Write-Error "[$env:_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME failed]"
    Write-Host  ""

    ErrorExit
}

# Cleanup

Write-Host "^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^"
Write-Host "^<                                                                                           ^>"
Write-Host "^>   The environment has been activated for this repository and is ready for development.    ^<"
Write-Host "^<                                                                                           ^>"
Write-Host "^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^v^^"
Write-Host ""
Write-Host ""

$env:_ACTIVATE_ERROR_LEVEL=0
ExitScript