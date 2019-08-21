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
            self._new_tokens += self.Tokens[
                self._original_token_index : start_token_index
            ]

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
        comments = []

        # ----------------------------------------------------------------------
        def CompleteLine():
            add_newline = False

            while comments:
                # Put each comment on its own line. We can do this because we ensure
                # that any split-able object with embedded comments will be broken up
                # into multiple lines.
                comment = comments.pop(0)

                if add_newline:
                    lines.append(black.Line())

                if lines[-1].leaves:
                    lines[-1].comments = [comment]
                else:
                    comment[1].type = black.STANDALONE_COMMENT
                    lines[-1].leaves.append(comment[1])

                add_newline = True

        # ----------------------------------------------------------------------

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
                if lines and (lines[-1].leaves or comments):
                    CompleteLine()

                    lines.append(black.Line())
                    lines[-1].depth = depth

                    prefix_line_count = 0
                else:
                    prefix_line_count += 1

            elif token.type == python_tokens.COMMENT:
                comments.append((len(lines[-1].leaves) + len(lines[-1].comments) - 1, token))

            else:
                if prefix_line_count != 0:
                    assert not lines[-1].leaves
                    token.prefix = "\n" * prefix_line_count
                    prefix_line_count = 0

                lines[-1].leaves.append(token)

        CompleteLine()

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
        self._token_modifications           = None

        super(BlackTokenizer, self).__init__()

    # ----------------------------------------------------------------------
    @Interface.DerivedProperty
    def Tokens(self):
        if self._tokens is None:
            tokens = []
            token_modifications = {}

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
                    line_tokens = list(line_tokens)
                    assert line_tokens

                    for comment_index, comment in reversed(line.comments):
                        assert comment_index <= len(line_tokens), (
                            comment_index,
                            len(line_tokens),
                        )
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
                        token_modifications[id(line_tokens[0])] = line_tokens[0].prefix

                        line_tokens[0].prefix = line_tokens[0].prefix[newline_ctr:]

                # Convert the STANDALONE_COMMENT type to COMMON to simplify plugin development.
                # When we construct lines, restore this type.
                line_token_index = 0
                while line_token_index < len(line_tokens):
                    token = line_tokens[line_token_index]
                    line_token_index += 1

                    if token.type != black.STANDALONE_COMMENT:
                        continue

                    token.type = python_tokens.COMMENT

                tokens += line_tokens
                tokens += [self.NEWLINE]

            self._tokens = tokens
            self._token_modifications = token_modifications

        return self._tokens

    # ----------------------------------------------------------------------
    def ToBlackLines(self):
        if not self.HasModifications():
            # Restore the modifications that were previously made
            if self._token_modifications:
                for line in self._lines:
                    for token in line.leaves:
                        token.prefix = self._token_modifications.get(
                            id(token),
                            token.prefix,
                        )

                self._token_modifications = None

            return self._lines

        return super(BlackTokenizer, self).ToBlackLines()
