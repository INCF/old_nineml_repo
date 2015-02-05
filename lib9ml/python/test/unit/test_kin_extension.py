"""
Tests for the user_layer module
"""


import unittest
from lxml import etree
from nineml.user_layer import Property
from nineml.abstraction_layer import Unit, Dimension
from nineml.document import Document

import os
import nineml
from nineml.user_layer import kinetic_extension
from nineml.user_layer import BaseULObject # just a wrapper for BaseNineMLObject

from nineml import read
import nineml.abstraction_layer as al
from nineml.abstraction_layer  import dynamics
from nineml.abstraction_layer.dynamics import kinetic_extension

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


rel_dir = os.path.join(os.path.dirname(__file__), 'test_kin_extension.xml')
print rel_dir, 'rel_dir', os.getcwd()


#wrap this in a class later.
#class KineticExtension(unittest.TestCase):

#ke=kinetic_extension.KineticExtension()
doc=read(rel_dir)
xml = etree.parse('/home/russell/git/nineml/lib9ml/python/test/unit/test_kin_extension.xml')
xml = etree.parse(rel_dir)
#nineml.document.load('/home/russell/git/nineml/lib9ml/python/test/unit/test_kin_extension.xml')
root = xml.getroot()
contents=nineml.load(root)
print etree.tostring(root)
print contents


#etree.tostring(contents)
#pe.from_xml(e,document)
#a=KineticExtension()    
    #response = Component.from_xml(e.find(NINEML + 'Component') or
    #                                  e.find(NINEML + 'Reference'),
    #                                  document))
    #ke.from_xml()
    #p2 = ke.from_xml('/home/russell/git/nineml/lib9ml/python/test/unit/test_kin_extension.xml')

    #p1 = Property("tau_m", 20.0, mV)
    #element = p1.to_xml()
    #xml = etree.tostring(element, pretty_print=True)
    #self.assertEqual(p1, p2)



class ModelTest(unittest.TestCase):
    pass


class DefinitionTest(unittest.TestCase):
    pass


class BaseComponentTest(unittest.TestCase):
    pass


class SpikingNodeTypeTest(unittest.TestCase):
    pass


class SynapseTypeTest(unittest.TestCase):
    pass


class CurrentSourceTypeTest(unittest.TestCase):
    pass


class StructureTest(unittest.TestCase):
    pass


class ConnectionRuleTest(unittest.TestCase):
    pass


class ConnectionTypeTest(unittest.TestCase):
    pass


class RandomDistributionTest(unittest.TestCase):
    pass


class ParameterTest(unittest.TestCase):

    def test_xml_roundtrip(self):
        p1 = Property("tau_m", 20.0, mV)
        element = p1.to_xml()
        xml = etree.tostring(element, pretty_print=True)
        p2 = Property.from_xml(element, Document(mV=mV))
        self.assertEqual(p1, p2)


class ParameterSetTest(unittest.TestCase):
    pass


class ValueTest(unittest.TestCase):
    pass


class StringValueTest(unittest.TestCase):
    pass


class GroupTest(unittest.TestCase):
    pass


class PopulationTest(unittest.TestCase):
    pass




class PositionListTest(unittest.TestCase):
    pass


class OperatorTest(unittest.TestCase):
    pass


class SelectionTest(unittest.TestCase):
    pass


class ProjectionTest(unittest.TestCase):
    pass
