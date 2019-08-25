# ----------------------------------------------------------------------
# |
# |  Tokenizer.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-22 12:23:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Tokenizer object"""

import os
import sys

if sys.version_info[0] != 2:
    import black
    from blib2to3.pygram import token as python_tokens

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Tokenizer(Interface.Interface):
    """Object that can be used to modify tokens before/after black processing"""

    # ----------------------------------------------------------------------
    # |  Types
    class FakeBlackLeaf(object):
        """Object that approximates a black.Leaf object by implementing functionality common only to custom decoration"""

        # ----------------------------------------------------------------------
        def __init__(self, value):
            self.value                      = value

            self.parent                     = None
            self.prefix                     = ""
            self.type                       = None

        # ----------------------------------------------------------------------
        def __eq__(self, other):
            return self.__dict__ == other.__dict__

        # ----------------------------------------------------------------------
        def __repr__(self):
            return "FakeBlackLeaf(None, '{}')".format(self.value)

    # ----------------------------------------------------------------------
    INDENT                                  = FakeBlackLeaf("++++")
    DEDENT                                  = FakeBlackLeaf("----")
    NEWLINE                                 = FakeBlackLeaf("\n")

    FAKE_TOKENS                             = [INDENT, DEDENT, NEWLINE]

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self):
        self._new_tokens                    = None
        self._original_token_index          = None

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def Tokens(self):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    def HasModifications(self):
        return bool(self._new_tokens)

    # ----------------------------------------------------------------------
    def ReplaceTokens(self, start_token_index, end_token_index, new_tokens):
        # ----------------------------------------------------------------------
        def ShouldReplace():
            if len(new_tokens) != end_token_index - start_token_index - 1:
                return True

            for new_token_index, new_token in enumerate(new_tokens):
                original_token = self.Tokens[start_token_index + new_token_index]

                if new_token != original_token:
                    return True

            return False

        # ----------------------------------------------------------------------

        # Only replace the content if there is a difference
        if not ShouldReplace():
            return

        if self._new_tokens is None:
            self._new_tokens = []
            self._original_token_index = 0

        assert start_token_index >= self._original_token_index, (
            start_token_index,
            self._original_token_index,
        )
        if start_token_index > self._original_token_index:
            self._new_tokens += self.Tokens[self._original_token_index : start_token_index]

        self._new_tokens += new_tokens
        self._original_token_index = end_token_index + 1

    # ----------------------------------------------------------------------
    def Commit(self):
        if not self.HasModifications():
            return self

        if self._original_token_index < len(self.Tokens):
            self._new_tokens += self.Tokens[self._original_token_index :]
            self._original_token_index = len(self.Tokens)

        return StandardTokenizer(self._new_tokens)

    # ----------------------------------------------------------------------
    def ToBlackLines(self):
        lines = [black.Line()]

        prefix_line_count = 0
        depth = 0

        for token in self.Tokens:
            if token == self.INDENT:
                depth += 1
                lines[-1].depth += 1

            elif token == self.DEDENT:
                assert depth
                depth -= 1

                assert lines[-1].depth
                lines[-1].depth -= 1

            elif token == self.NEWLINE:
                if lines and lines[-1].leaves:
                    lines.append(black.Line())
                    lines[-1].depth = depth

                    prefix_line_count = 0
                else:
                    prefix_line_count += 1

            elif token.type == python_tokens.COMMENT:
                if not lines[-1].leaves or lines[-1].comments:
                    token.prefix = "\n" * prefix_line_count
                    token.type = black.STANDALONE_COMMENT

                    lines[-1].leaves.append(token)

                else:
                    lines[-1].comments.append((len(lines[-1].leaves), token))

            else:
                if prefix_line_count != 0:
                    assert not lines[-1].leaves
                    token.prefix = "\n" * prefix_line_count
                    prefix_line_count = 0

                lines[-1].leaves.append(token)

        return lines


# ----------------------------------------------------------------------
class StandardTokenizer(Tokenizer):
    """Tokenizer whose tokens are based on a list of tokens"""

    # ----------------------------------------------------------------------
    def __init__(self, tokens):
        self._tokens                        = tokens

        super(StandardTokenizer, self).__init__()

    # ----------------------------------------------------------------------
    @Interface.DerivedProperty
    def Tokens(self):
        return self._tokens


# ----------------------------------------------------------------------
class BlackTokenizer(Tokenizer):
    """Tokenizer whose tokens are based on lines produced by black"""

    # ----------------------------------------------------------------------
    def __init__(self, lines):
        self._lines                         = lines

        self._tokens                        = None
        self._restore_funcs                 = None

        super(BlackTokenizer, self).__init__()

    # ----------------------------------------------------------------------
    @Interface.DerivedProperty
    def Tokens(self):
        if self._tokens is None:
            tokens = []
            restore_funcs = []

            depth = 0

            for line in self._lines:
                depth_delta = line.depth - depth

                if depth_delta != 0:
                    if depth_delta > 0:
                        tokens += [self.INDENT] * depth_delta
                    elif depth_delta < 0:
                        tokens += [self.DEDENT] * -depth_delta
                    else:
                        assert False, depth_delta

                    depth = line.depth

                # Merge the line's comments into its tokens
                line_tokens = line.leaves
                if line.comments:
                    # Get the index of the last valid token. Sometimes lines end with
                    # tokens without values.
                    last_valid_token_index = len(line_tokens) - 1
                    while (
                        last_valid_token_index > 0 and not line_tokens[last_valid_token_index].value
                    ):
                        last_valid_token_index -= 1

                    line_tokens = list(line_tokens)
                    assert line_tokens

                    for comment_index, comment in reversed(line.comments):
                        assert comment_index <= len(line_tokens), (comment_index, len(line_tokens))

                        if comment_index < last_valid_token_index:
                            line_tokens.insert(comment_index + 1, self.NEWLINE)

                        line_tokens.insert(comment_index + 1, comment)

                if line_tokens and line_tokens[0].prefix:
                    newline_ctr = 0

                    while (
                        newline_ctr < len(line_tokens[0].prefix)
                        and line_tokens[0].prefix[newline_ctr] == "\n"
                    ):
                        newline_ctr += 1

                    if newline_ctr != 0:
                        tokens += [self.NEWLINE] * newline_ctr

                        # Preserve the original prefix value so that it can be restored if no other modifications
                        # have been made. This is a hack, but black gets confused when introducing deep copies of
                        # tokens as it breaks previous- and next-based relationships.

                        # ----------------------------------------------------------------------
                        def RestoreTokenPrefix(
                            token=line_tokens[0],                           # <Cell variable defined in loop> pylint: disable = W0640
                            prefix=line_tokens[0].prefix,                   # <Cell variable defined in loop> pylint: disable = W0640
                        ):
                            token.prefix = prefix

                        # ----------------------------------------------------------------------

                        restore_funcs.append(RestoreTokenPrefix)

                        line_tokens[0].prefix = line_tokens[0].prefix[newline_ctr:]

                # Convert the STANDALONE_COMMENT type to COMMON to simplify plugin development.
                # When we construct lines, restore this type.
                line_token_index = 0
                while line_token_index < len(line_tokens):
                    token = line_tokens[line_token_index]
                    line_token_index += 1

                    if token.type != black.STANDALONE_COMMENT:
                        continue

                    # ----------------------------------------------------------------------
                    def RestoreTokenType(
                        token=token,
                    ):
                        token.type = black.STANDALONE_COMMENT

                    # ----------------------------------------------------------------------

                    restore_funcs.append(RestoreTokenType)

                    token.type = python_tokens.COMMENT
                    token._python_formatter_is_standalone_comment = True    # <Access to a protected member> pylint: disable = W0212

                    # Insert a newline if there are tokens that follow this one
                    if len(line_tokens) > 1:
                        line_tokens.insert(line_token_index, self.NEWLINE)
                        line_token_index += 1

                tokens += line_tokens
                tokens += [self.NEWLINE]

            self._tokens = tokens
            self._restore_funcs = restore_funcs

        return self._tokens

    # ----------------------------------------------------------------------
    def ToBlackLines(self):
        restore_funcs = self._restore_funcs or []
        self._restore_funcs = None

        if not self.HasModifications():
            for restore_func in restore_funcs:
                restore_func()

            return self._lines

        return super(BlackTokenizer, self).ToBlackLines()
