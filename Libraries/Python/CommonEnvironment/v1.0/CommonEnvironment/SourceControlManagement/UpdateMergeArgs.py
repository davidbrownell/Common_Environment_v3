# ----------------------------------------------------------------------
# |  
# |  UpdateMergeArgs.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-17 16:29:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains various types used for updates and merges"""

import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Too few public methods> pylint: disable = R0903

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class EmptyUpdateMergeArg(object):
    """Tip on the current branch"""

    def __repr__(self):
        return "<SCM-specific tip>"

# ----------------------------------------------------------------------
class ChangeUpdateMergeArg(object):
    """A specific change"""

    def __init__(self, change):
        self.Change                         = change

    def __repr__(self):
        return self.Change

# ----------------------------------------------------------------------
class DateUpdateMergeArg(object):
    """Change nearest to the date on the current branch"""

    def __init__(self, date, greater_than=None):
        self.Date                           = date
        self.GreaterThan                    = greater_than

    def __repr__(self):
        operator = ''
        if self.GreaterThan is not None:
            operator = '>' if self.GreaterThan else '<'

        return "{}{}".format(operator, self.Date)

# ----------------------------------------------------------------------
class BranchUpdateMergeArg(object):
    """Tip on specified branch"""

    def __init__(self, branch):
        self.Branch                         = branch

    def __repr__(self):
        return self.Branch

# ----------------------------------------------------------------------
class BranchAndDateUpdateMergeArg(DateUpdateMergeArg):
    """Change nearest to the date on the specified branch"""

    def __init__(self, branch, date, greater_than=None):
        self.Branch                         = branch
        super(BranchAndDateUpdateMergeArg, self).__init__(date, greater_than=greater_than)

    def __repr__(self):
        return "{} ({})".format( self.Branch,
                                 super(BranchAndDateUpdateMergeArg, self).__repr__(),
                               )

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def FromCommandLine( change=None,
                     branch=None,
                     date=None,
                     date_greater_than=None,
                   ):
    if change:
        return ChangeUpdateMergeArg(change)

    if branch and date:
        return BranchAndDateUpdateMergeArg(branch, date, greater_than=date_greater_than)

    if branch:
        return BranchUpdateMergeArg(branch)

    if date:
        return DateUpdateMergeArg(date, greater_than=date_greater_than)

    return EmptyUpdateMergeArg()
