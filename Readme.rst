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
Windows                   Cmd.exe                 Windows 10 April 2018 Update
Windows                   PowerShell              Windows 10 April 2018 Update
Linux                     Bash                    Ubuntu 18.04, 16.04
========================  ======================  =========================================
  
Definitions
===========
.. _Tool:

Tool
  BugBug

.. _Script:

Script
  BugBug
  
.. _Library:

Library
  BugBug

.. _Repository:

Repository
  BugBug
  
.. _Environment:

Environment
  BugBug

.. _`Version Spec`:

Version Specs
  When a repository takes a dependency_ on another, version spec(ifications) can be used to activate specific versions of Tools_ and Libraries_ in those repositories. 
  
    The latest version of a Tool_ or Library_ is used if not customized by a version spec.
  
  ``VersionSpecs`` is defined in `RepositoryBootstrap/SetupAndActivate/Configuration.py <RepositoryBootstrap/SetupAndActivate/Configuration.py>`_ and is specified in a repository's ``Setup_custom.py`` file.

.. _Dependency:

Dependencies
  BugBug
    
.. _Tools: Tool_
.. _Scripts: Script_
.. _Libraries: Library_
.. _Repositories: Repository_
.. _Environments: Environment_
.. _`Version Specs`: `Version Spec`_
.. _Dependencies: Dependency_

Functionality
=============
.. _`Python Bootstrap`:

Python Bootstrap
  BugBug

.. _`Build Tools`:

Build Tools
  BugBug

 .. _`Test Tools`:
 
Test Tools
  BugBug

.. _`Code Coverage Tools`:

Code Coverage Tools
  BugBug

Docker Images
=============
Docker images of Common_Environment are generated periodically.

==========================  ==========================================
Coming Soon                 An environment that is setup_ but not activated_ (useful as a base image).
Coming Soon                 An environment that is activated_.
==========================  ==========================================

Dependencies
============
As this repository serves as the foundation for all other repositories, it has no dependencies.

Related Repositories
--------------------
==========================  ==========================================
Coming Soon                 TODO
==========================  ==========================================

Creating Your Own Repository
============================
`CreateRepository.py <RepositoryBootstrap/CreateRepository.py>`_ is an interactive script used to create a new repository_ based on the Common_Environment framework.

From an activated_ environment_, run:

  =========================  =======================================
  Linux                      ``python $DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/RepositoryBootstrap/CreateRepository.py <Destination Repository Dir> <Repository Name>``
  Windows                    ``python %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\RepositoryBootstrap\CreateRepository.py <Destination Repository Dir> <Repository Name>``
  =========================  =======================================
  
  The script will prompt you for information and then generated the necessary files in ``<Destination Repository Dir>``.
  
Support
=======
For question or issues, please visit https://github.com/davidbrownell/v3-Common_Environment/issues.