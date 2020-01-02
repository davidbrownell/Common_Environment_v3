# ----------------------------------------------------------------------
# |
# |  GroupEmptyParensPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 15:36:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Plugin import PluginBase       # <unable to import> pylint: disable = E0401
from PythonFormatterImpl.Tokenizer import Tokenizer     # <unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Removes any newlines placed between empty parens/brackets/braces"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("GroupEmptyParens")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def DecorateTokens(
        tokenizer,
        tokenize_func,                      # <Unused argument> pylint: disable = W0613
        recurse_count,                      # <Unused argument> pylint: disable = W0613
    ):
        for token_index, token in enumerate(tokenizer.Tokens):
            if token_index == 0:
                continue

            if token_index + 1 == len(tokenizer.Tokens):
                continue

            if token != Tokenizer.NEWLINE:
                continue

            prev_token_value = tokenizer.Tokens[token_index - 1].value
            next_token_value = tokenizer.Tokens[token_index + 1].value

            if (
                (prev_token_value == "(" and next_token_value == ")")
                or (prev_token_value == "[" and next_token_value == "]")
                or (prev_token_value == "{" and next_token_value == "}")
            ):
                tokenizer.ReplaceTokens(token_index, token_index + 1, [])
