# ----------------------------------------------------------------------
# |  
# |  setup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-08-15 1:28:37
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
from setuptools import setup, find_packages

# Do the setup
setup( name="CommonEnvironment",
       version="1.0.1",
       packages=find_packages(),
       install_requires=[ "asciitree >= 0.3.3", 
                          "colorama >= 0.3.9", 
                          "enum34 >= 1.1.6", 
                          "inflect >= 0.2.5", 
                          "six >= 1.11.0", 
                          "tqdm >= 4.23.3", 
                          "wrapt >= 1.10.11"
                        ],
       
       author="David Brownell",
       author_email="pypi@DavidBrownell.com",
       description="Foundational Python libraries used across a variety of different projects and environments.",
       long_description=open("Readme.rst").read(),
       license="Boost Software License",
       keywords=[ "Python",
                  "Library",
                  "Development",
                  "Foundation",
                ],
       url="https://github.com/davidbrownell/Common_Environment_v3",
       project_urls={ "Bug Tracker" : "https://github.com/davidbrownell/Common_Environment_v3/issues",
                    },
       classifiers=[ "Development Status :: 5 - Production/Stable",
                     "Intended Audience :: Developers",
                     "License :: OSI Approved :: Boost Software License 1.0 (BSL-1.0)",
                     "Natural Language :: English",
                     "Operating System :: OS Independent",
                     "Programming Language :: Python",
                     "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
     )
