"""
  At this stage, this file is just a stub as the compilation of biophysical
  components is done by a Scheme package, which at this time is called "NeMo"
  (which conflicts with a simulator of the same name) but is likely to change
  at a later point
"""

import urllib
from lxml import etree
from lxml.builder import E

biophysical_cells_namespace = 'http://www.nineml.org/Biophysics'
BIO_NINEML = "{%s}" % biophysical_cells_namespace
from nineml.base import NINEML


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
    if root.tag == NINEML + 'nineml':
        root = next(root.iterchildren())
    for element in root.findall(BIO_NINEML + BiophysicsModel.element_name):
        biophysics_model = BiophysicsModel.from_xml(element)
        biophysics_models[biophysics_model.name] = biophysics_model
    return biophysics_models


class BiophysicsModel(object):

    element_name = 'Biophysics'

    def __init__(self, name, components, component_classes, build_hints=None):
        self.name = name
        self.components = components
        self.component_classes = component_classes
        self.build_hints = build_hints

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
        component_classes = {}
        for comp_class_elem in element.findall(BIO_NINEML +
                                               ComponentClass.element_name):
            component_class = ComponentClass.from_xml(comp_class_elem)
            component_classes[component_class.name] = component_class
        for comp_elem in element.findall(BIO_NINEML + Component.element_name):
            component = Component.from_xml(comp_elem, component_classes)
            if (component.name == '__NO_COMPONENT__' and
                '__NO_COMPONENT__' in components):
                components['__NO_COMPONENT__'].parameters.\
                                                   update(component.parameters)
            else:
                components[component.name] = component
        build_hints_elem = element.find(BIO_NINEML + BuildHints.element_name)
        if build_hints_elem is not None:
            build_hints = BuildHints.from_xml(build_hints_elem)
        else:
            raise Exception("Did not find required build hints tag in "
                            "biophysics block")
        return cls(element.attrib['name'], components, component_classes,
                   build_hints)


class ComponentClass(object):

    element_name = 'ComponentClass'

    def __init__(self, name, comp_class_type):
        self.name = name
        self.type = comp_class_type

    def __repr__(self):
        return ("Component Class '{}' of type '{}'"
                .format(self.name, self.type))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 type=self.type)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        return cls(element.attrib['name'], element.attrib['type'])


class Component(object):

    element_name = 'Component'

    def __init__(self, name, parameters, comp_type):
        self.name = name
        self.parameters = parameters
        self.type = comp_type

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
    def from_xml(cls, element, component_classes):
        assert element.tag == BIO_NINEML + cls.element_name
        parameters = {}
        if element.attrib.has_key('definition'):
            comp_class = component_classes[element.attrib['definition']]
            comp_type = comp_class.type
        else:
            comp_type = element.attrib.get('type', None)
        name = element.attrib.get('name', None)
        if comp_type in ('defaults', 'globals', 'membrane-capacitance',
                         'geometry'):
            name = '__NO_COMPONENT__'
        elif name == '__NO_COMPONENT__':
            raise Exception("Component name '{}' clashes with an internal "
                            "variable name, please select another"
                            .format(name))
        properties_element = element.find(BIO_NINEML + 'properties')
        # FIXME This is a temporary hack until all cases are standardised
        # between either being enclosed in a properties tag or not.
        if properties_element is not None:
            param_elements = properties_element.findall(BIO_NINEML +
                                                        Parameter.element_name)
        else:
            param_elements = element.findall(BIO_NINEML +
                                             Parameter.element_name)
        for child in param_elements:
            parameter = Parameter.from_xml(child)
            parameters[parameter.name] = parameter
        return cls(name, parameters, comp_type)


class Parameter(object):

    element_name = 'Parameter'

    def __init__(self, name, value, unit):
        self.name = name
        self.value = value
        self.unit = unit

    def __repr__(self):
        return ("Parameter '{}' = {} ({})".format(self.name, self.value,
                                                  self.unit if self.unit else
                                                              'dimensionless'))

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
        value = element.find(BIO_NINEML + 'value').text
        if value.startswith('('):
            value = value[1:]
        if value.endswith(')'):
            value = value[:-1]
        value = float(value)
        unit_elem = element.find(BIO_NINEML + 'unit')
        if unit_elem is not None:
            unit = unit_elem.text
        else:
            unit = None
        return cls(element.attrib['name'], value, unit)


class BuildHints(object):

    element_name = 'BuildHints'

    def __init__(self, builders):
        self._builders = builders

    def __getitem__(self, key):
        return self._builders[key]

    def __repr__(self):
        return ("BuildHints for {} builders(s)"
                .format(len(self._builders)))

    def to_xml(self):
        return E(self.element_name,
                 *[c.to_xml() for c in self._builders])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        builders = {}
        for child in element.findall(BIO_NINEML + Builder.element_name):
            builder = Builder.from_xml(child)
            builders[builder.name] = builder
        return cls(builders)


class Builder(object):

    element_name = 'Builder'

    def __init__(self, name, simulators):
        self.name = name
        self._simulators = simulators

    def __getitem__(self, key):
        return self._simulators[key]

    def __repr__(self):
        return ("Build hints for {} builder for {} simulators(s)"
                .format(self.name, len(self._simulators)))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[c.to_xml() for c in self._simulators])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        simulators = {}
        for child in element.findall(BIO_NINEML + Simulator.element_name):
            simulator = Simulator.from_xml(child)
            simulators[simulator.name] = simulator
        return cls(element.attrib['name'], simulators)


class Simulator(object):

    element_name = 'Simulator'

    def __init__(self, name, method=None, kinetic_components=[]):
        self.name = name
        self.method = method
        self.kinetic_components = kinetic_components

    def __repr__(self):
        return ("Build hints for the '{}' simulator"
                .format(self.name))

    def to_xml(self):
        optional_components = []
        if self.method:
            optional_components.append(E('Method', self.method))
        optional_components.extend([E('KineticComponent', kc)
                                    for kc in self.kinetic_components])
        return E(self.element_name,
                 name=self.name,
                 *optional_components)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_NINEML + cls.element_name
        method_elem = element.find(BIO_NINEML + 'Method')
        method = method_elem.text.strip() if method_elem is not None else None
        kinetic_components = []
        for child in element.findall(BIO_NINEML + 'KineticComponent'):
            kinetic_components.append(child.text.strip())
        return cls(element.attrib['name'], method, kinetic_components)
