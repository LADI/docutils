#!/usr/bin/env python3

# $Id$
# Author: Lea Wiemann <LeWiemann@gmail.com>
# Copyright: This module has been placed in the public domain.

"""
Test for docutils XML writer.

.. Attention::
   While the tests compare the output on the string-level, no guarantee
   is given against changes to identical XML representations like
   ``<empty></empty>`` vs. ``<empty/>``. The sample strings in this test
   module mirrors the current behaviour of the docutils_xml writer.
"""


if __name__ == '__main__':
    import __init__
from test_writers import DocutilsTestSupport # before importing docutils!
import docutils
import docutils.core

from io import StringIO

# sample strings
# --------------

source = """\
Test

----------

Test. \xe4\xf6\xfc\u20ac"""

xmldecl = """<?xml version="1.0" encoding="iso-8859-1"?>
"""

doctypedecl = """\
<!DOCTYPE document PUBLIC "+//IDN docutils.sourceforge.net\
//DTD Docutils Generic//EN//XML"\
 "http://docutils.sourceforge.net/docs/ref/docutils.dtd">
"""

generatedby = '<!-- Generated by Docutils %s -->\n' % docutils.__version__

bodynormal = """\
<document source="&lt;string&gt;"><paragraph>Test</paragraph>\
<transition></transition><paragraph>Test. \xe4\xf6\xfc&#8364;</paragraph>\
</document>"""

bodynewlines = """\
<document source="&lt;string&gt;">
<paragraph>Test</paragraph>
<transition></transition>
<paragraph>Test. \xe4\xf6\xfc&#8364;</paragraph>
</document>
"""

bodyindents = """\
<document source="&lt;string&gt;">
    <paragraph>Test</paragraph>
    <transition></transition>
    <paragraph>Test. \xe4\xf6\xfc&#8364;</paragraph>
</document>
"""

# raw XML
# """""""

raw_xml_source = """\
.. raw:: xml

   <root>
    <child>Test \xe4\xf6\xfc\u20ac</child>
    &gt;
    &lt;

   </root>

.. role:: xml(raw)
   :format: xml

:xml:`<test>inline raw XML</test>`.
"""

raw_xml = """\
<document source="&lt;string&gt;">
<raw format="xml" xml:space="preserve"><root>
 <child>Test \xe4\xf6\xfc&#8364;</child>
 &gt;
 &lt;

</root></raw>
<paragraph><raw classes="xml" format="xml" xml:space="preserve">\
<test>inline raw XML</test></raw>.</paragraph>
</document>
"""

invalid_raw_xml_source = """\
.. raw:: xml

   <root>
    <child>Test \xe4\xf6\xfc\u20ac</child>
   </mismatch>

.. role:: xml(raw)
   :format: xml

:xml:`<test>inline raw XML&lt;/test>`.
"""

invalid_raw_xml = """\
<document source="&lt;string&gt;">
<raw format="xml" xml:space="preserve"><root>
 <child>Test \xe4\xf6\xfc\u20ac</child>
</mismatch></raw>
<paragraph><raw classes="xml" format="xml" xml:space="preserve">\
<test>inline raw XML&lt;/test></raw>.</paragraph>
</document>
"""


def publish_xml(settings, source):
    return docutils.core.publish_string(source=source.encode('utf8'),
                                        reader_name='standalone',
                                        writer_name='docutils_xml',
                                        settings_overrides=settings)

# XML Test Case
# -------------

class DocutilsXMLTestCase(DocutilsTestSupport.StandardTestCase):

    settings = {'input_encoding': 'utf8',
                'output_encoding': 'iso-8859-1',
                '_disable_config': True,
                'indents': False,
                'newlines': True,
                'xml_declaration': False,
                'doctype_declaration': False,
               }

    def test_publish(self):
        settings = self.settings.copy()
        settings['newlines'] = False
        for settings['xml_declaration'] in True, False:
            for settings['doctype_declaration'] in True, False:
                expected = ''
                if settings['xml_declaration']:
                    expected += xmldecl
                if settings['doctype_declaration']:
                    expected += doctypedecl
                expected += generatedby
                expected += bodynormal
                result = publish_xml(settings, source)
                self.assertEqual(result, expected.encode('latin1'))

    def test_publish_indents(self):
        settings = self.settings.copy()
        settings['indents'] = True
        result = publish_xml(settings, source)
        expected = (generatedby + bodyindents).encode('latin1')
        self.assertEqual(result, expected)

    def test_publish_newlines(self):
        settings = self.settings.copy()
        result = publish_xml(settings, source)
        expected = (generatedby + bodynewlines).encode('latin1')
        self.assertEqual(result, expected)

    def test_raw_xml(self):
        result = publish_xml(self.settings, raw_xml_source)
        expected = (generatedby
                    + raw_xml).encode('latin1', 'xmlcharrefreplace')
        self.assertEqual(result, expected)

    def test_invalid_raw_xml(self):
        warnings = StringIO()
        settings = self.settings.copy()
        settings['warning_stream'] = warnings
        result = publish_xml(settings, invalid_raw_xml_source)
        expected = (generatedby
                    + invalid_raw_xml).encode('latin1', 'xmlcharrefreplace')
        self.assertEqual(result, expected)
        warnings.seek(0)
        self.assertEqual(
            warnings.readlines(),
            ['<string>:5: '
             '(WARNING/2) Invalid raw XML in column 2, line offset 3:\n',
             '<root>\n',
             ' <child>Test \xe4\xf6\xfc\u20ac</child>\n',
             '</mismatch>\n',
             '<string>:10: '
             '(WARNING/2) Invalid raw XML in column 30, line offset 1:\n',
             '<test>inline raw XML&lt;/test>\n'])
        settings['halt_level'] = 2 # convert info messages to exceptions
        settings['warning_stream'] = ''
        self.assertRaises(docutils.utils.SystemMessage,
                          publish_xml, settings, invalid_raw_xml_source)


if __name__ == '__main__':
    import unittest
    unittest.main()
