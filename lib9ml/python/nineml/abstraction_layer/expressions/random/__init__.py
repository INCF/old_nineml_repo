from lxml import etree
from lxml.builder import ElementMaker
import os.path
from nineml.abstraction_layer import BaseALObject
from nineml.exceptions import NineMLRuntimeError
from nineml.xmlns import uncertml_namespace, UNCERTML


class RandomVariable(BaseALObject):

    element_name = 'RandomVariable'
    defining_attributes = ('name', 'distribution', 'units')

    def __init__(self, name, distribution, units):
        self.name = name
        self.distribution = distribution
        self.units = units

    def __repr__(self):
        return ("RandomVariable(name={}, units={}, distribution={})"
                .format(self.name, self.distribution, self.units))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomvariable(self, **kwargs)

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    def set_units(self, units):
        assert self.units == units, \
            "Renaming units with ones that do not match"
        self.units = units


class RandomDistribution(BaseALObject):
    """
    A base class for reading and writing distributions defined in UncertML
    """

    # Load UncertML schema from file
    with open(os.path.join(os.path.dirname(__file__), 'uncertml.xsd')) as f:
        uncertml_schema = etree.XMLSchema(etree.parse(f))

    E = ElementMaker(namespace=uncertml_namespace,
                     nsmap={"un": uncertml_namespace})

    valid_distributions = ('normal',)

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def to_xml(self):
        return self.E(self.name + 'Distribution',
                      *(self.E(n, str(v))
                        for n, v in self.parameters.iteritems()))

    @classmethod
    def from_xml(cls, element, document):  # @UnusedVariable
        if not cls.uncertml_schema.validate(element):
            error = cls.uncertml_schema.error_log.last_error
            raise NineMLRuntimeError(
                "Invalid UncertML XML in Random distribution: {} - {}\n\n{}"
                .format(error.domain_name, error.type_name,
                        etree.tostring(element, pretty_print=True)))
        if not element.tag.endswith('Distribution'):
            raise NineMLRuntimeError(
                "Only UncertML distribution elements can be used inside "
                "RandomVariable elements, not '{}'".format(element.tag))
        name = element.tag[len(UNCERTML):-len('Distribution')]
        params = dict((c.tag[len(UNCERTML):], float(c.text))
                      for c in element.getchildren())
        return cls(name=name, parameters=params)
