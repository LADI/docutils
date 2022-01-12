#!/usr/bin/env python3
# :Copyright: © 2020 Günter Milde.
# :License: Released under the terms of the `2-Clause BSD license`_, in short:
#
#    Copying and distribution of this file, with or without modification,
#    are permitted in any medium without royalty provided the copyright
#    notice and this notice are preserved.
#    This file is offered as-is, without any warranty.
#
# .. _2-Clause BSD license: https://opensource.org/licenses/BSD-2-Clause
#
# Revision: $Revision$
# Date: $Date$
"""
A parser for CommonMark Markdown text using `recommonmark`__.

__ https://pypi.org/project/recommonmark/

.. important:: This module is provisional

   * The "recommonmark" package is unmaintained and deprecated.
     This wrapper module will be removed in a future Docutils version.

   * The API is not settled and may change with any minor Docutils version.
"""

import docutils.parsers
from docutils import nodes, Component

try:
    from recommonmark.parser import CommonMarkParser
except ImportError as err:
    missing_dependency_msg = '%s.\nParsing "recommonmark" Markdown flavour ' \
        'requires the package https://pypi.org/project/recommonmark' % err
    raise ImportError(missing_dependency_msg)


# recommonmark 0.5.0 introduced a hard dependency on Sphinx
# https://github.com/readthedocs/recommonmark/issues/202
# There is a PR to change this to an optional dependency
# https://github.com/readthedocs/recommonmark/pull/218
try:
    from sphinx import addnodes
except ImportError:
    # create a stub
    class addnodes(nodes.pending): pass


class Parser(CommonMarkParser):
    """MarkDown parser based on recommonmark.

    This parser is provisional:
    the API is not settled and may change with any minor Docutils version.
    """
    supported = ('recommonmark', 'commonmark', 'markdown', 'md')
    config_section = 'recommonmark parser'
    config_section_dependencies = ('parsers',)

    def get_transforms(self):
        return Component.get_transforms(self) # + [AutoStructify]

    def parse(self, inputstring, document):
        """Use the upstream parser and clean up afterwards.
        """
        # check for exorbitantly long lines
        for i, line in enumerate(inputstring.split('\n')):
            if len(line) > document.settings.line_length_limit:
                error = document.reporter.error(
                    'Line %d exceeds the line-length-limit.'%(i+1))
                document.append(error)
                return

        # pass to upstream parser
        try:
            CommonMarkParser.parse(self, inputstring, document)
        except Exception as err:
            if document.settings.traceback:
                raise err
            error = document.reporter.error('Parsing with "recommonmark" '
                                            'returned the error:\n%s'%err)
            document.append(error)

        # Post-Processing
        # ---------------

        # merge adjoining Text nodes:
        for node in document.findall(nodes.TextElement):
            children = node.children
            i = 0
            while i+1 < len(children):
                if (isinstance(children[i], nodes.Text)
                    and isinstance(children[i+1], nodes.Text)):
                    children[i] = nodes.Text(children[i]+children.pop(i+1))
                    children[i].parent = node
                else:
                    i += 1

        # add "code" class argument to literal elements (inline and block)
        for node in document.findall(lambda n: isinstance(n,
                                (nodes.literal, nodes.literal_block))):
            if 'code' not in node['classes']:
                node['classes'].append('code')
        # move "language" argument to classes
        for node in document.findall(nodes.literal_block):
            if 'language' in node.attributes:
                node['classes'].append(node['language'])
                del node['language']

        # replace raw nodes if raw is not allowed
        if not document.settings.raw_enabled:
            for node in document.findall(nodes.raw):
                warning = document.reporter.warning('Raw content disabled.')
                node.parent.replace(node, warning)

        # drop pending_xref (Sphinx cross reference extension)
        for node in document.findall(addnodes.pending_xref):
            reference = node.children[0]
            if 'name' not in reference:
                reference['name'] = nodes.fully_normalize_name(
                                                    reference.astext())
            node.parent.replace(node, reference)

    def visit_document(self, node):
        """Dummy function to prevent spurious warnings.

        cf. https://github.com/readthedocs/recommonmark/issues/177
        """
        pass

    # Overwrite parent method with version that
    # doesn't pass deprecated `rawsource` argument to nodes.Text:
    def visit_text(self, mdnode):
        self.current_node.append(nodes.Text(mdnode.literal))
