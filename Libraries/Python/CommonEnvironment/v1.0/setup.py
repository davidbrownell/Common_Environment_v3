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
import os
import re
import sys

import pip
from setuptools import setup, find_packages
import six

from CommonEnvironment import Process

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# Get the installed packages. We can assume that everything installed is a dependency since we
#  are the most fundamental repo.
installation_requirements = []

sink = six.moves.StringIO()

result = Process.Execute("pip freeze", sink)
sink = sink.getvalue()

assert result == 0, sink

regex = re.compile(r"^(?P<name>.+?)==(?P<version>.+)$")

for line in sink.split('\n'):
    match = regex.match(line)
    if not match:
        continue

    installation_requirements.append("{}>={}".format(match.group("name"), match.group("version")))

# Do the setup
setup( name="CommonEnvironment",
       version="1.0",
       packages=find_packages(),
       install_requires=installation_requirements,
       
       author="David Brownell",
       author_email="pypi@DavidBrownell.com",
       description="Foundational Python libraries used across a variety of different projects and environments.",
       long_description=open(os.path.join(_script_dir, "Readme.rst")).read(),
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
