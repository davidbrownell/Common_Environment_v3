==================
Common_Environment
==================

Foundational repository_ that implements functionality common to all development environments_, including:

  * Dynamic repository_ relationship management
  * Tool_, Script_, and Library_ dependency management
  * `Build tools`_
  * `Test tools`_
  * `Code Coverage tools`_
  * Python bootstrapping_ activities
  
.. _bootstrapping: `Python Bootstrap`_

Contents
========
#. `Quick Start`_
#. License_
#. `Supported Platforms`_
#. Definitions_
#. Functionality_
#. `Docker Images`_
#. `Pip Install`_
#. Dependencies_
#. `Creating Your Own Repository`_
#. Support_

Quick Start
===========
`Setup`_ and `Activate`_ are required to begin using this repository.

.. _Setup:

Setup
  Setup installs/unpacks tools used during development activities and locates its repository dependencies (if any). Setup must be run on your machine after cloning the repository or after changing the file location of repositories that it depends upon (if any).

  ====================================  =====================================================
  Linux                                 ``Setup.sh``
  Windows                               ``Setup.cmd``
  Windows (PowerShell)                  ``Setup.ps1``
  ====================================  =====================================================
  
.. _Activate:

Activate
  Activate prepares the current environment for development activities and must be run at least once in each terminal window.
  
  ====================================  =====================================================
  Linux                                 ``Activate.sh <python36|python27>``
  Windows                               ``Activate.cmd <python36|python27>``
  Windows (PowerShell)                  ``Activate.ps1 <python36|python27>``
  ====================================  =====================================================

.. _Activated: Activate_
.. _Activation: Activate_
  
License
=======
Common_Environment is licensed under the `Boost Software License <https://www.boost.org/LICENSE_1_0.txt>`_. 

`GitHub <https://github.com>`_ describes this license as:

  A simple permissive license only requiring preservation of copyright and license notices for source (and not binary) distribution. Licensed works, modifications, and larger works may be distributed under different terms and without source code.

This repository distributes the following software:

========================================  =========================================
Software                                  License
========================================  =========================================
`OpenSSL <https://www.openssl.org/>`_     `OpenSSL License <https://www.openssl.org/source/license.html>`_
`Pandoc <https://pandoc.org/>`_           `GNU GPL v2 <https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html>`_
`Python <https://www.python.org>`_        `PSF License Agreement <https://docs.python.org/3/license.html>`_
========================================  =========================================
  
Supported Platforms
===================
This software has been verified on the following platforms.

========================  ======================  =========================================
Platform                  Scripting Environment   Version
========================  ======================  =========================================
Windows                   Cmd.exe                 Windows 10:

                                                  - October 2018 Update
                                                  - April 2018 Update

Windows                   PowerShell              Windows 10:

                                                  - October 2018 Update
                                                  - April 2018 Update

Linux                     Bash                    Ubuntu:

                                                  - 18.04
                                                  - 16.04
========================  ======================  =========================================
  
Definitions
===========
.. _Tool:

Tool
  A folder available in the environment's path after activation. A specific tool version can be specified using `Version Specs`_.

.. _Script:

Script
  Content available in the environment's path after activation. Scripts do not have specific versions.
  
.. _Library:

Library
  A language-specific library available after activation; where the specifics of "availability" are based on the corresponding language. In Python, this means that the library is made available within the Python's site-packages directory. A specific library version can be specified using `Version Specs`_.

.. _Repository:

Repository
  A collection of code based on Common_Environment. A repository and those that it depends on are activated within an environment.
  
.. _Environment:

Environment
  A repository that has been activated within a command window. Environments leverage Tools_, Scripts_, and Libraries_ it defines or are defined in any repository that it depends on.

.. _`Version Spec`:

Version Specs
  When a repository takes a dependency_ on another, version spec(ifications) can be used to activate specific versions of Tools_ and Libraries_ in those repositories. 
  
    The latest version of a Tool_ or Library_ is used if not customized by a version spec.
  
  ``VersionSpecs`` is defined in `RepositoryBootstrap/SetupAndActivate/Configuration.py <RepositoryBootstrap/SetupAndActivate/Configuration.py>`_ and is specified in a repository's ``Setup_custom.py`` file.

.. _Dependency:

Dependencies
  Repositories can be dependent upon other repositories. During activation, all Tools_, Scripts_, and Libraries_ from those repositories will be made available in addition to any Tools_, Scripts_, and Libraries_ made available by the current repository.

.. _Configuration:
  
Configuration
  A repository may support configurations, where an individual configuration customizes `Version Specs`_ for the Tools_, Scripts_, and Libraries_ made available during activation. For example, the Common_Environment repository makes 2 configurations available: ``python36`` and ``python27``. 
  
  Configurations are defined in a repository's ``Setup_custom.py`` file.
  
.. _Tools: Tool_
.. _Scripts: Script_
.. _Libraries: Library_
.. _Repositories: Repository_
.. _Environments: Environment_
.. _`Version Specs`: `Version Spec`_
.. _Dependencies: Dependency_
.. _Configurations : Configuration_

Functionality
=============
.. _`Python Bootstrap`:

Python Bootstrap
  Support for environment-specific instances of Python, each with distinct Libraries_. Different environments with different Python library `Version Specs`_ can safely coexist on the same system. 
  
  This functionality is similar to a dynamic virtualenv.

.. _`Build Tools`:

Build Tools
  Plugin-based system for the arbitrary building of applications. For more information, see:
  
  * `Builder.py <Scripts/Builder.py>`_ to invoke a build
  * `BuildImpl/__init__.py <Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/BuildImpl/__init__.py>`_ to implement a build

  ====================================  =====================================================
  Linux                                 ``Builder.sh /?``
  Windows                               ``Builder.cmd /?``
  Windows (PowerShell)                  ``Builder.ps1 /?``
  ====================================  =====================================================
  
 .. _`Test Tools`:
 
Test Tools
  Plugin-based system for the arbitrary testing of applications. For more information, see:
  
  * `Tester.py <Scripts/Tester.py>`_ to execute tests
  * `Compilers/PythonVerifier.py <Scripts/Compilers/PythonVerifier.py>`_ for an example of a test compiler plugin
  * `TestParsers/PyUnittestTestParser.py <Scripts/TestParsers/PyUnittestTestParser.py>`_ for an example of a test framework plugin
  * `TestParserImpl/__init__.py <Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/TestParserImpl/__init__.py>`_ to implement a test parser plugin
  
  ====================================  =====================================================
  Linux                                 ``Tester.sh /?``
  Windows                               ``Tester.cmd /?``
  Windows (PowerShell)                  ``Tester.ps1 /?``
  ====================================  =====================================================
  
.. _`Code Coverage Tools`:

Code Coverage Tools
  Plugin-based system for the arbitrary extraction of code coverage information. For more information, see:
  
  * `Tester.py <Scripts/Tester.py>`_ to execute tests
  * `TestExecutor/PyCoverageTestExecutor.py <Scripts/TestExecutor/PyCoverageTestExecutor.py>`_ for an example of a code coverage / test executor plugin
  * `TestExecutorImpl/__init__.py <Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/TestExecutorImpl/__init__.py>`_ to implement a test executor / code coverage extractor plugin
  
  ====================================  =====================================================
  Linux                                 ``Tester.sh /?``
  Windows                               ``Tester.cmd /?``
  Windows (PowerShell)                  ``Tester.ps1 /?``
  ====================================  =====================================================

Docker Images
=============
Docker images of Common_Environment are generated periodically.

================================================  ==========================================
dbrownell/common_environment:python36             An environment that is activated_ with python36.
dbrownell/common_environment:python27             An environment that is activated_ with python27.
dbrownell/common_environment:base                 An environment that is setup_ but not activated_ (useful as a base image for other Common_Environment-based images).
================================================  ==========================================

Pip Install
===========
Common_Environment's implementation includes foundational `python tools and functionality <Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment>`_ that is useful outside of 
the repository itself.

A wheel file with these tools are generated periodically and available via `pip <https://pypi.org/project/pip/>`_:

  ``pip install Common-Environment-v3``

Dependencies
============
As this repository serves as the foundation for all other repositories, it has no dependencies.

Related Repositories
--------------------
=======================================================================================  ==========================================
`Common_EnvironmentEx <https://github.com/davidbrownell/Common_EnvironmentEx>`_          Enhances Common_Environment with libraries, scripts, and tools common to different development activities. 
=======================================================================================  ==========================================

Creating Your Own Repository
============================
`CreateRepository.py <RepositoryBootstrap/CreateRepository.py>`_ is an interactive script used to create a new repository_ based on the Common_Environment framework.

From an activated_ environment_, run:

  =========================  =======================================
  Linux                      ``python $DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/RepositoryBootstrap/CreateRepository.py <Destination Repository Dir> <Repository Name>``
  Windows                    ``python %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\CreateRepository.py <Destination Repository Dir> <Repository Name>``
  Windows (PowerShell)       ``python $env:DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL\RepositoryBootstrap\CreateRepository.py <Destination Repository Dir> <Repository Name>``
  =========================  =======================================
  
  The script will prompt you for information and then generate the necessary files in ``<Destination Repository Dir>``.
  
Support
=======
For question or issues, please visit https://github.com/davidbrownell/Common_Environment_v3/issues.
