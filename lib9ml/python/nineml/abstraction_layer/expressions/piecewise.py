from itertools import chain
from .. import BaseALObject
from .base import Expression


class Piecewise(BaseALObject):

    element_name = 'Piecewise'
    defining_attributes = ('name', 'value', 'units')

    def __init__(self, name, pieces, otherwise, units):
        self.name = name
        self.pieces = pieces
        self.otherwise = otherwise
        self.units = units

    def __repr__(self):
        return ("Piecewise(name={}, value={}, units={})"
                .format(self.name, self.value, self.units))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_constant(self, **kwargs)

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    def set_units(self, units):
        assert self.units == units, \
            "Renaming units with ones that do not match"
        self.units = units

    @property
    def rhs_atoms(self):
        return set(*chain([p.rhs_atoms for p in self.pieces] +
                          [self.otherwise.rhs_atoms]))


class Piece(BaseALObject, Expression):

    element_name = "Otherwise"
    defining_attributes = ('_rhs', 'condition')

    def __init__(self, expr, condition):
        super(Piece, self).__init__(expr)
        if isinstance(condition, basestring):
            condition = Condition(condition)
        self.condition = condition

    @property
    def rhs_atoms(self):
        return chain(super(Piece, self).rhs_atoms + self.condition.rhs_atoms)


class Otherwise(BaseALObject, Expression):

    element_name = "Otherwise"


class Condition(BaseALObject, Expression):

    element_name = "Condition"


