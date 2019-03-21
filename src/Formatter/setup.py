# ----------------------------------------------------------------------
# |
# |  setup.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-08-15 1:28:37
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
from setuptools import setup, find_packages

# Do the setup
setup(
    name="CommonEnvironment-Formatter",
    version="0.5.0-b1",
    packages=find_packages(),
    install_requires=["CommonEnvironment >= 1.0.6", "black >= 18.9.b0"],
    scripts=["bin/Formatter", "bin/Formatter.cmd"],
    author="David Brownell",
    author_email="pypi@DavidBrownell.com",
    description="Formats Python code using Black (https://github.com/ambv/black) plus enhancements.",
    long_description=open("Readme.rst").read(),
    license="Boost Software License",
    keywords=[
        "Python",
        "Library",
        "Development",
        "Foundation",
    ],
    url="https://github.com/davidbrownell/Common_Environment_v3",
    project_urls={"Bug Tracker": "https://github.com/davidbrownell/Common_Environment_v3/issues"},
    classifiers=[
        "Development Status :: 4 - Beta",                                   # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Boost Software License 1.0 (BSL-1.0)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
