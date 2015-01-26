from .. import BaseALObject
from .base import Expression


class Piecewise(BaseALObject):

    element_name = 'Piecewise'
    defining_attributes = ('name', 'value', 'units')

    def __init__(self, name, value, units):
        self.name = name
        self.value = value
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


class Piece(BaseALObject, Expression):

    def __init__(self, expr, condition):
        super(Piece, self).__init__(expr)
        self.condition = condition


class Otherwise(BaseALObject, Expression):
    pass


class Condition(BaseALObject, Expression):
    pass
