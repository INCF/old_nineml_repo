"""
  At this stage, this file is just a stub as the compilation of biophysical components is done by a 
  Scheme package, which at this time is called "NeMo" (which conflicts with a simulator of the same
  name) but is likely to change at a later point
"""

import urllib
from itertools import chain
from lxml import etree
from lxml.builder import E

biophysical_cells_namespace = 'http://www.nineml.org/Biophysics'
BIO_NINEML = "{%s}" % biophysical_cells_namespace

def parse(url):
    """
    Read a NineML user-layer file and return a Model object.

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if not isinstance(url, file):
        f = urllib.urlopen(url)
        doc = etree.parse(f)
        f.close()
    else:
        doc = etree.parse(url)
    root = doc.getroot()
    biophysics_models = {}
    for element in root.findall(BIO_NINEML + BiophysicsModel.element_name):
        biophysics_model = BiophysicsModel.from_xml(element)
        biophysics_models[biophysics_model.name] = biophysics_model
    return biophysics_models


class BiophysicsModel(object):

    element_name = 'Biophysics'

    def __init__(self, name, components):
        self.name = name
        self.components = components

    def __repr__(self):
        return ("BiophysicsModel '{}' with {} components(s)"
                .format(self.name, len(self.components)))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[c.to_xml() for c in self.components.values()])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        components = {}
        for child in element.getchildren():
            if child.tag == BIO_NINEML + Component.element_name:
                component = Component.from_xml(child)
                components[component.name] = component
        return cls(element.attrib['name'], components)
    
    
class Component(object):

    element_name = 'Component'

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def __repr__(self):
        return ("Component '{}' with {} parameters(s)"
                .format(self.name, len(self.parameters)))

    def to_xml(self):
        kwargs = {}
        if self.name:
            kwargs['name'] = self.name
        return E(self.element_name,
                 *[c.to_xml() for c in self.parameters.values()],
                 **kwargs)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        parameters = {}
        param_elements = element.find(BIO_NINEML+'properties')
        if param_elements is not None:
            for child in param_elements.getchildren():
                if child.tag == BIO_NINEML + Parameter.element_name:
                    parameter = Parameter.from_xml(child)
                    parameters[parameter.name] = parameter
        return cls(element.attrib.get('name', None), parameters)    
    
    
class Parameter(object):

    element_name = 'Parameter'

    def __init__(self, name, value, unit):
        self.name = name
        self.value = value
        self.unit = unit

    def __repr__(self):
        return ("Parameter '{}' = {} {}".format(self.name, self.value, self.unit))

    def to_xml(self):
        opt_args = []
        if self.unit:
            opt_args.append(E('unit', self.unit))
        return E(self.element_name,
                 E('value', self.value),
                 name=self.name,
                 *opt_args)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        value = element.find(BIO_NINEML+'value').text
        unit_elem = element.find(BIO_NINEML+'unit')
        if unit_elem is not None:
            unit = unit_elem.text
        else:
            unit = None
        return cls(element.attrib['name'], value, unit)  
        