"""
This file contains the definitions for the Events

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from copy import deepcopy
import sympy
from nineml.utils import ensure_valid_identifier, filter_discrete_types
from nineml.abstraction_layer.componentclass import BaseALObject
from ..expressions import Expression, ExpressionWithSimpleLHS
from ...exceptions import (NineMLRuntimeError,
                           NineMLInvalidElementTypeException)
from .utils.cloner import DynamicsCloner


class Transition(BaseALObject):

    defining_attributes = ('_state_assignments', '_event_outputs',
                           '_target_regime_name')

    def __init__(self, state_assignments=None, event_outputs=None,
                 target_regime_name=None):
        """Abstract class representing a transition from one |Regime| to
        another.

        |Transition| objects are not created directly, but via the subclasses
        |OnEvent| and |OnCondition|.

        :param state_assignments: A list of the state-assignments performed
            when this transition occurs. Objects in this list are either
            `string` (e.g A = A+13) or |StateAssignment| objects.
        :param event_outputs: A list of |OutputEvent| objects emitted when
            this transition occurs.
        :param target_regime_name: The name of the regime to go into after this
            transition.  ``None`` implies staying in the same regime. This has
            to be specified as a string, not the object, because in general the
            |Regime| object is not yet constructed. This is automatically
            resolved by the |DynamicsClass| in
            ``_ResolveTransitionRegimeNames()`` during construction.


        .. todo::

            For more information about what happens at a regime transition, see
            here: XXXXXXX

        """
        super(Transition, self).__init__()
        if target_regime_name:
            assert isinstance(target_regime_name, basestring)

        # Load state-assignment objects as strings or StateAssignment objects
        state_assignments = state_assignments or []

        sa_types = (basestring, StateAssignment)
        sa_type_dict = filter_discrete_types(state_assignments, sa_types)
        sa_from_str = [StateAssignment.from_str(o)
                       for o in sa_type_dict[basestring]]
        self._state_assignments = dict(
            (sa.lhs, sa) for sa in sa_type_dict[StateAssignment] + sa_from_str)

        self._event_outputs = event_outputs or []

        self._target_regime_name = target_regime_name
        self._source_regime_name = None

        # Set later, once attached to a regime:
        self._target_regime = None
        self._source_regime = None

    def set_source_regime(self, source_regime):
        """ Internal method, used during component construction.

        Used internally by the DynamicsClass objects after all objects have be
        constructed, in the ``_ResolveTransitionRegimeNames()`` method. This is
        because when we build Transitions, the Regimes that they refer to
        generally are not build yet, so are referred to by strings. This method
        is used to set the source ``Regime`` object. We check that the name of
        the object set is the same as that previously expected.
        """

        assert isinstance(source_regime, Regime)
        assert not self._source_regime
        if self._source_regime_name:
            assert self._source_regime_name == source_regime.name
        else:
            self._source_regime_name = source_regime.name
        self._source_regime = source_regime

    # MH: I am pretty sure we don't need this, but its possible,
    # so I won't delete it yet - since there might be a reason we do :)
    # def set_target_regime_name(self, target_regime_name):
    #    assert False
    #    assert isinstance( target_regime_name, basestring)
    #    assert not self._target_regime
    #    assert not self._target_regime_name
    #    self._target_regime_name = target_regime_name

    def set_target_regime(self, target_regime):
        """ Internal method, used during component construction.

            See ``set_source_regime``
        """
        assert isinstance(target_regime, Regime)
        if self._target_regime:
            assert id(self.target_regime) == id(target_regime)
            return

        # Did we already set the target_regime_name
        if self._target_regime_name:
            assert self._target_regime_name == target_regime.name
        else:
            self._target_regime_name = target_regime.name
        self._target_regime = target_regime

    @property
    def target_regime_name(self):
        """DO NOT USE: Internal function. Use `target_regime.name` instead.
        """
        if self._target_regime_name:
            assert isinstance(self._target_regime_name, basestring)
        return self._target_regime_name

    @property
    def source_regime_name(self):
        """DO NOT USE: Internal function. Use `source_regime.name` instead.
        """
        if self._source_regime:
            err = ("Should not be called by users.Use source_regime.name "
                   "instead")
            raise NineMLRuntimeError(err)
        assert self._source_regime_name
        return self._source_regime_name

    @property
    def target_regime(self):
        """Returns the target regime of this transition.

        .. note::

            This method will only be available after the DynamicsClass
            containing this transition has been built. See
            ``set_source_regime``
        """

        assert self._target_regime
        return self._target_regime

    @property
    def source_regime(self):
        """Returns the source regime of this transition.

        .. note::

            This method will only be available after the |DynamicsClass|
            containing this transition has been built. See
            ``set_source_regime``
        """
        assert self._source_regime
        return self._source_regime

    @property
    def state_assignments(self):
        return self._state_assignments.itervalues()

    def state_assignment(self, variable):
        return self._state_assignments[variable]

    @property
    def state_assignment_variables(self):
        return self._state_assignments.iterkeys()

    @property
    def event_outputs(self):
        """|Events| that happen when this transitions occurs"""
        return self._event_outputs

    def add(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments[element.name] = element
        elif isinstance(element, OutputEvent):
            self._output_events[element.name] = element
        raise NineMLInvalidElementTypeException(
            "Could not add element of type '{}' to {} class"
            .format(element.__class__.__name__, self.__class__.__name__))

    def remove(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments.pop(element.name)
        elif isinstance(element, OutputEvent):
            self._output_events.pop(element.name)
        raise NineMLInvalidElementTypeException(
            "Could not remove element of type '{}' to {} class"
            .format(element.__class__.__name__, self.__class__.__name__))


class OnEvent(Transition):

    defining_attributes = (Transition.defining_attributes + ('src_port_name',))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_onevent(self, **kwargs)

    def __init__(self, src_port_name, state_assignments=None,
                 event_outputs=None, target_regime_name=None):
        """Constructor for ``OnEvent``

            :param src_port_name: The name of the |EventPort| that triggers
            this transition

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        Transition.__init__(self, state_assignments=state_assignments,
                            event_outputs=event_outputs,
                            target_regime_name=target_regime_name)
        self._src_port_name = src_port_name.strip()
        ensure_valid_identifier(self._src_port_name)

    @property
    def src_port_name(self):
        return self._src_port_name

    def __repr__(self):
        return """OnEvent( %s )""" % self.src_port_name

    @property
    def _name(self):
        """
        This is included to allow OnEvents to be polymorphic with
        other named structures
        """
        return self.src_port_name


class OnCondition(Transition):

    defining_attributes = (Transition.defining_attributes + ('trigger',))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_oncondition(self, **kwargs)

    def __init__(self, trigger, state_assignments=None,
                 event_outputs=None, target_regime_name=None):
        """Constructor for ``OnEvent``

            :param trigger: Either a |Trigger| object or a ``string`` object
                specifying the conditions under which this transition should
                occur.

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        if isinstance(trigger, Trigger):
            self._trigger = DynamicsCloner().visit(trigger)
        elif isinstance(trigger, basestring):
            self._trigger = Trigger(rhs=trigger)
        else:
            assert False

        Transition.__init__(self, state_assignments=state_assignments,
                            event_outputs=event_outputs,
                            target_regime_name=target_regime_name)

    def __repr__(self):
        return 'OnCondition( %s )' % self.trigger.rhs

    @property
    def trigger(self):
        return self._trigger

    @property
    def _name(self):
        """
        This is included to allow OnConditions to be polymorphic with
        other named structures
        """
        return self.trigger.rhs


class Trigger(BaseALObject, Expression):

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_trigger(self, **kwargs)

    def __init__(self, rhs):
        BaseALObject.__init__(self)
        Expression.__init__(self, rhs)

    def __repr__(self):
        return "Trigger('%s')" % (self.rhs)

    @property
    def reactivate_condition(self):
        negated = deepcopy(self)
        negated.negate()
        return negated


class StateAssignment(BaseALObject, ExpressionWithSimpleLHS):

    """Assignments represent a change that happens to the value of a
    ``StateVariable`` during a transition between regimes.

    For example, in an integrate-and-fire neuron, we may want to reset the
    voltage back to zero, after it has reached a certain threshold. In this
    case, we would have an ``OnCondition`` object, that is triggered when
    ``v>vthres``. Attached to this OnCondition transition, we would attach an
    StateAssignment which sets ``v=vreset``.

    The left-hand-side symbol must be a state-variable of the component.

    """

    def __init__(self, lhs, rhs):
        """StateAssignment Constructor

        `lhs` -- A `string`, which must be a state-variable of the
                 componentclass.
        `rhs` -- A `string`, representing the new value of the state after
                 this assignment.

        """
        BaseALObject.__init__(self)
        ExpressionWithSimpleLHS.__init__(self, lhs=lhs, rhs=rhs)

    @property
    def name(self):
        """
        This is included to allow State-assignments to be polymorphic with
        other named structures
        """
        return self.lhs

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_assignment(self, **kwargs)

    def __repr__(self):
        return "StateAssignment('%s', '%s')" % (self.lhs, self.rhs)

    @classmethod
    def from_str(cls, state_assignment_string):
        """Creates an StateAssignment object from a string"""
        lhs, rhs = state_assignment_string.split('=')
        return StateAssignment(lhs=lhs, rhs=rhs)


class OutputEvent(BaseALObject):

    """OutputEvent

    OutputEvents can occur during transitions, and correspond to
    an event being generated on the relevant EventPort port in
    the component.
    """

    defining_attributes = ('port_name',)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_outputevent(self, **kwargs)

    def __init__(self, port_name):
        """OutputEvent Constructor

        :param port: The name of the output EventPort that should
            transmit an event. An `EventPort` with a mode of 'send' must exist
            with a corresponding name in the componentclass, otherwise a
            ``NineMLRuntimeException`` will be raised.

        """
        super(OutputEvent, self).__init__()
        self._port_name = port_name.strip()
        ensure_valid_identifier(self._port_name)

    @property
    def port_name(self):
        '''Returns the name of the port'''
        return self._port_name

    def __str__(self):
        return 'OutputEvent( port: %s )' % self.port_name

    def __repr__(self):
        return "OutputEvent('%s')" % self.port_name

    @property
    def _name(self):
        """
        This is included to allow State-assignments to be polymorphic with
        other named structures
        """
        return self.port_name

from .regimes import Regime
