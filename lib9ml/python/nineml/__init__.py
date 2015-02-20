"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from itertools import chain
from operator import and_
import nineml


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self):
        self.annotations = None

    def __eq__(self, other):
        if not (isinstance(other, self.__class__) or
                isinstance(self, other.__class__)):
            return False
        for name in self.defining_attributes:
            self_elem = getattr(self, name)
            other_elem = getattr(other, name)
            if not isinstance(self_elem, dict):
                # Try to sort the elements (so they are order non-specific) if
                # they are an iterable list, ask forgiveness and fall back to
                # standard equality if they aren't
                try:
                    self_elem = sorted(self_elem, key=lambda x: x._name)
                    other_elem = sorted(other_elem, key=lambda x: x._name)
                except (TypeError, AttributeError):
                    pass
            if self_elem != other_elem:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        raise NotImplementedError(
            "Derived class '{}' has not overriden accept_visitor method."
            .format(self.__class__.__name__))


class TopLevelObject(object):

    @property
    def attributes_with_dimension(self):
        return []  # To be overridden in derived classes

    @property
    def attributes_with_units(self):
        return []  # To be overridden in derived classes

    @property
    def all_units(self):
        return [a.units for a in self.attributes_with_units]

    @property
    def all_dimensions(self):
        return [a.dimension for a in self.attributes_with_dimension]

    def write(self, fname):
        """
        Writes the top-level NineML object to file in XML.
        """
        write(self, fname)  # Calls nineml.document.Document.write


import abstraction_layer
import user_layer
import exceptions
from abstraction_layer import Unit, Dimension
from document import read, write, load, Document
