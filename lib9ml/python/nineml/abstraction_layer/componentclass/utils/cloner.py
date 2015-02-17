"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError
from ...expressions.utils import is_builtin_symbol
from .visitors import ComponentActionVisitor, ComponentVisitor


class ComponentExpandPortDefinition(ComponentActionVisitor):

    def __init__(self, originalname, targetname):

        super(ComponentExpandPortDefinition, self).__init__(
            require_explicit_overrides=False)
        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.name_transform_inplace(self.namemap)


class ComponentExpandAliasDefinition(ComponentActionVisitor):

    """ An action-class that walks over a component, and expands an alias in
    Assignments, Aliases, TimeDerivatives and Conditions
    """

    def __init__(self, originalname, targetname):

        super(ComponentExpandAliasDefinition, self).__init__(
            require_explicit_overrides=False)
        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.rhs_name_transform_inplace(self.namemap)


class ComponentCloner(ComponentVisitor):

    def prefix_variable(self, variable, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        if variable in prefix_excludes:
            return variable

        if is_builtin_symbol(variable):
            return variable

        else:
            return prefix + variable

    def visit_parameter(self, parameter, **kwargs):
        return parameter.__class__(
            name=self.prefix_variable(parameter.name, **kwargs),
            dimension=parameter.dimension)

    def visit_alias(self, alias, **kwargs):
        new_alias = alias.__class__(lhs=alias.lhs, rhs=alias.rhs)
        name_map = dict([(a, self.prefix_variable(a, **kwargs))
                         for a in new_alias.atoms])
        new_alias.name_transform_inplace(name_map=name_map)
        # FIXME:? TGC 1/15 Doesn't the LHS need updating too?
        return new_alias

    def visit_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_randomvariable = randomvariable.__class__(
            name=randomvariable.name, value=randomvariable.value,
            units=randomvariable.units)
        return new_randomvariable

    def visit_constant(self, constant, **kwargs):  # @UnusedVariable
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_constant = constant.__class__(
            name=constant.name, value=constant.value, units=constant.units)
        return new_constant

    def visit_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_piecewise = piecewise.__class__(
            name=piecewise.name, pieces=piecewise.pieces,
            otherwise=piecewise.otherwise, units=piecewise.units)
        return new_piecewise
