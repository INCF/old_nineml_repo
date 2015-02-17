"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ..base import Parameter
from .cloner import DynamicsExpandPortDefinition
from ...ports import AnalogSendPort, AnalogReducePort, AnalogReceivePort
from nineml.utils import filter_expect_single
from nineml.exceptions import NineMLRuntimeError
from ...componentclass.utils.modifiers import (
    ComponentModifier, ComponentRenameIdentiferModifier)


class DynamicPortModifier(ComponentModifier):

    """Utility classes for modifying components"""

    _ExpandPortDefinition = DynamicsExpandPortDefinition

    @classmethod
    def close_analog_port(cls, componentclass, port_name, value="0"):
        """Closes an incoming analog port by assigning its value to 0"""

        if not componentclass.is_flat():
            raise NineMLRuntimeError('close_analog_port() on non-flat '
                                     'componentclass')

        # Subsitute the value in:
        componentclass.accept_visitor(cls._ExpandPortDefinition(port_name,
                                                                value))

        # Remove it from the list of ports:
        port = filter_expect_single(componentclass.analog_ports,
                                    lambda ap: ap.name == port_name)
        if isinstance(port, AnalogSendPort):
            componentclass._analog_send_ports.pop(port_name)
        elif isinstance(port, AnalogReceivePort):
            componentclass._analog_receive_ports.pop(port_name)
        elif isinstance(port, AnalogReducePort):
            componentclass._analog_reduce_ports.pop(port_name)
        else:
            raise TypeError("Expected an analog port")

    @classmethod
    def close_all_reduce_ports(cls, componentclass, exclude=None):
        """
        Closes all the ``reduce`` ports on a componentclass by assigning them a
        value of 0
        """
        if not componentclass.is_flat():
            raise NineMLRuntimeError('close_all_reduce_ports() on non-flat '
                                     'componentclass')

        for arp in componentclass.query.analog_reduce_ports:
            if exclude and arp.name in exclude:
                continue
            cls.close_analog_port(componentclass=componentclass,
                                  port_name=arp.name, value='0')

    @classmethod
    def rename_port(cls, componentclass, old_port_name, new_port_name):
        """ Renames a port in a componentclass """
        if not componentclass.is_flat():
            raise NineMLRuntimeError('rename_port() on non-flat '
                                     'componentclass')

        # Find the old port:
        port = filter_expect_single(componentclass.analog_ports,
                                    lambda ap: ap.name == old_port_name)
        port._name = new_port_name

    @classmethod
    def remap_port_to_parameter(cls, componentclass, port_name):
        """ Renames a port in a componentclass """
        if not componentclass.is_flat():
            raise NineMLRuntimeError('rename_port_to_parameter() on non-flat '
                                     'componentclass')

        # Find the old port:
        port = filter_expect_single(componentclass.analog_ports,
                                    lambda ap: ap.name == port_name)
        componentclass._analog_ports.remove(port)

        # Add a new parameter:
        componentclass._parameters[port_name] = Parameter(port_name)


class DynamicsRenameIdentiferModifier(ComponentRenameIdentiferModifier):

    def action_statevariable(self, statevariable, **kwargs):  # @UnusedVariable
        if self.old_name == statevariable.name:
            self._found_lhs = True
            statevariable.name = self.new_name

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        timederivative.rhs = self._sub_into_rhs(timederivative.rhs)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self._rename_lhs(port)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._rename_lhs(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self._rename_lhs(port)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self._rename_lhs(port)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._rename_lhs(port)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        self._rename_lhs(assignment)
        assignment.rhs = self._sub_into_rhs(assignment.rhs)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        trigger.rhs = self._sub_into_rhs(trigger.rhs)

    def action_onevent(self, onevent, **kwargs):  # @UnusedVariable
        if onevent.src_port_name == self.from_name:
            onevent.src_port_name = self.to_name
