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


class ComponentRenameSymbol(ComponentActionVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def __init__(self, componentclass, old_symbol_name, new_symbol_name):
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=True)
        self.old_symbol_name = old_symbol_name
        self.new_symbol_name = new_symbol_name
        self.namemap = {old_symbol_name: new_symbol_name}

        if not componentclass.is_flat():
            raise NineMLRuntimeError('Rename Symbol called on non-flat model')

        self.lhs_changes = []
        self.rhs_changes = []
        self.port_changes = []

        self.visit(componentclass)
        componentclass.validate()

    def note_lhs_changed(self, what):
        self.lhs_changes.append(what)

    def note_rhs_changed(self, what):
        self.rhs_changes.append(what)

    def note_port_changed(self, what):
        self.port_changes.append(what)

    def action_componentclass(self, component, **kwargs):
        pass

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if parameter.name == self.old_symbol_name:
            parameter._name = self.new_symbol_name
            self.note_lhs_changed(parameter)

    def _action_port(self, port, **kwargs):  # @UnusedVariable
        if port.name == self.old_symbol_name:
            port._name = self.new_symbol_name
            self.note_port_changed(port)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.lhs == self.old_symbol_name:
            self.note_lhs_changed(alias)
            alias.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in alias.atoms:
            self.note_rhs_changed(alias)
            alias.name_transform_inplace(self.namemap)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable
        if randomvariable.name == self.old_symbol_name:
            self.note_lhs_changed(randomvariable)
            randomvariable.name_transform_inplace(self.namemap)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if constant.name == self.old_symbol_name:
            self.note_lhs_changed(constant)
            constant.name_transform_inplace(self.namemap)

    def action_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        if piecewise.name == self.old_symbol_name:
            self.note_lhs_changed(piecewise)
            piecewise.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in piecewise.atoms:
            self.note_rhs_changed(piecewise)
            piecewise.name_transform_inplace(self.namemap)


class ComponentClonerVisitor(ComponentVisitor):

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

    def visit_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_randomvariable = randomvariable.__class__(name=randomvariable.name,
                                          value=randomvariable.value,
                                          units=randomvariable.units)
        return new_randomvariable

    def visit_constant(self, constant, **kwargs):  # @UnusedVariable
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_constant = constant.__class__(name=constant.name,
                                          value=constant.value,
                                          units=constant.units)
        return new_constant
    
    def visit_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        # FIXME: This would be handled better by a copy constructor?? TGC 1/15
        new_piecewise = piecewise.__class__(name=piecewise.name,
                                            pieces=piecewise.pieces,
                                            otherwise=piecewise.otherwise,
                                            units=piecewise.units)
        return new_piecewise
