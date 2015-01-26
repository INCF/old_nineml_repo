from .. import BaseALObject


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

    valid_distributions = ('normal',)

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def to_xml(self):
        raise NotImplementedError

    @classmethod
    def from_xml(cls, element, document):
        raise NotImplementedError
