import os.path
from lxml import etree

if __name__ == '__main__':

    class unittest(object):

        class TestCase(object):

            def __init__(self):
                try:
                    self.setUp()
                except AttributeError:
                    pass

            def assertEqual(self, first, second):
                print 'are{} equal'.format(' not' if first != second else '')
else:
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest

from nineml.extensions.morphology import *  # @UnusedWildImport


class TestMorphology(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), 'data',
                             'test_morphology.9ml')

    def test_morphology(self):
        morph9ml = parse(self.test_file)
#         with open(self.test_file) as f:
#             test_file_text = f.read()
        etree.ElementTree(morph9ml.to_xml()).write(
                     os.path.join(os.path.dirname(self.test_file),
                                                  'test_morphology_out.9ml'),
                                               encoding="UTF-8",
                                               pretty_print=True,
                                               xml_declaration=True)
#         self.assertEqual(morph9ml_text, test_file_text)

if __name__ == '__main__':
    test = TestMorphology()
    test.test_morphology()
