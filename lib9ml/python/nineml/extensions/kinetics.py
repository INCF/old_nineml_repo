from nineml.abstraction_layer.dynamics import DynamicsBlock, regimes
from nineml.abstraction_layer import BaseALObject
from copy import copy, deepcopy
from nineml.abstraction_layer.expressions import (
    Expression, Alias, ExpressionSymbol)

from nineml.abstraction_layer.dynamics.utils.xml import DynamicsClassXMLLoader, DynamicsClassXMLWriter

from nineml import annotations 
from nineml import utils
from nineml.annotations import read_annotations
from nineml.abstraction_layer.units import dimensionless
from nineml.utils import ensure_valid_identifier, expect_single
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import normalise_parameter_as_list
from nineml.utils import filter_discrete_types
from nineml.abstraction_layer.dynamics import DynamicsClass 
from nineml.abstraction_layer.componentclass import ComponentClass, Parameter
from nineml.abstraction_layer.dynamics.utils import DynamicsQueryer
from nineml.utils import (check_list_contain_same_items, invert_dictionary,
                            assert_no_duplicates)

from nineml.abstraction_layer.dynamics.utils.cloner import (
    DynamicsExpandAliasDefinition, DynamicsCloner)
from itertools import chain
from nineml.abstraction_layer.dynamics.validators import DynamicsValidator
from nineml.abstraction_layer.dynamics.utils import DynamicsClassInterfaceInferer
from nineml.abstraction_layer.dynamics.base import _NamespaceMixin
from collections import Counter
from nineml.abstraction_layer.dynamics import TimeDerivative, Regime, StateVariable
from sympy import symbols
import sympy


def inf_check(l1, l2, desc):
    check_list_contain_same_items(l1, l2, desc1='Declared',
                                  desc2='Inferred', ignore=['t'], desc=desc)


class KineticDynamicsClass(DynamicsClass):
    defining_attributes = ('_name', '_parameters', '_analog_send_ports',
                           '_analog_receive_ports', '_analog_reduce_ports',
                           '_event_send_ports', '_event_receive_ports',
                           '_kineticsblock', '_kinetic_states',
                           '_reactions', '_constraints', '_main_block')

    def __init__(self, name,
                 parameters=None, analog_ports=[],
                 event_ports=[], aliases=None, constants=None,
                 kinetic_states=None, reactions=None, constraints=None,
                 kineticsblock=None):

        # We can specify in the componentclass, and they will get forwarded to
        # the dynamics class. We check that we do not specify half-and-half:
        if kineticsblock is not None:
            if (constraints is not None or reactions is not None
                    or kinetic_states is not None or aliases is not None):
                raise NineMLRuntimeError(
                    "Either specify a 'kineticdynamics' parameter, or "
                    "kinetic_states, reactions,constraints, but not both!")
        else:
            kineticsblock = KineticDynamicsBlock(
                kinetic_states=kinetic_states, reactions=reactions,
                constraints=constraints, constants=constants, aliases=aliases)

        print kineticsblock
        #super(KineticDynamicsClass, self).__init__(
        #    name=name, dynamicsblock=kineticsblock)


        #what the call to the constructor should be, once all of the correct 
        #parameters, units and AnalogReceivePort have been declared in the XML file.
        super(KineticDynamicsClass, self).__init__(
            name=name, parameters=parameters, event_ports=event_ports,
            analog_ports=analog_ports, dynamicsblock=kineticsblock)


    @property
    def reactions(self):
        return self._main_block.reactions.itervalues()

    def reaction(self, from_state, to_state):
        return self._main_block.reactions[tuple(sorted((from_state, to_state)))]

    @property
    def kinetic_states(self):
        return self._main_block.kinetic_states.itervalues()

    def kinetic_state(self, name):
        return self._main_block.kinetic_states[name]

    @property
    def kinetic_state_names(self):
        return self._main_block.kinetic_states.iterkeys()

    @property
    def constraints(self):
        return self._main_block.constraints

    def constraint(self, name):
        return self._main_block.constraints[name]

    @property
    def constraint_variables(self):
        return self._main_block.constraints.iterkeys()


class KineticDynamicsBlock(DynamicsBlock):

    """
    An object, which encapsulates a component's regimes, transitions,
    and state variables
    """

    defining_attributes = ('kinetic_states', 'aliases', 'reactions',
                           'constraints', 'constants')

    def __init__(self, kinetic_states=None, reactions=None, constraints=None,
                 constants=None, aliases=None):
                 #Note could have kinetic aliases instead of aliases 
                 #but want to inherit instead.
                 # regimes=None, aliases=None, state_variables=None,
                 #constants=None, piecewises=None, randomvariables=None, k

        """DynamicsBlock object constructor

           :param aliases: A list of aliases, which must be either |Alias|
               objects or ``string``s.
           :param regimes: A list containing at least one |Regime| object.
           :param state_variables: An optional list of the state variables,
                which can either be |StateVariable| objects or `string` s. If
                provided, it must match the inferred state-variables from the
                regimes; if it is not provided it will be inferred
                automatically.
        """

        aliases = normalise_parameter_as_list(aliases)
        kinetic_states = normalise_parameter_as_list(kinetic_states)
        reactions = normalise_parameter_as_list(reactions)
        constraints = normalise_parameter_as_list(constraints)

        # Load the KineticStates  as objects or strings:
        sv_types = (basestring, kinetic_states)

        # Kinetics specific members
     
        self.reactions = dict((tuple(sorted((r.from_state, r.to_state))), r)
                               for r in reactions)
        self.kinetic_states = dict((a.name, a) for a in kinetic_states)
        self.constraints = dict((c.state, c) for c in constraints)



  
        # constraints is a dictionary of constraint objects. 
        # the state attribute is the user defined state variable to use to solve the equation. 
        # The state attribute should be the same in all constraint objects, so I have
        # indexed into the first one.
        #for state in self.kinetic_states:

        
        #reduce_state = [self.kinetic_states[c.state] for c in self.constraints.itervalues()]
        #constraint_eq = [c.state for c in self.constraints.itervalues()]
   
        reduce_state = self.kinetic_states[constraints[0].state]
        constraint_eq = self.constraints[constraints[0].state]

        state_subs = deepcopy(constraint_eq.rhs) #clone the object.
        #such that do not corrupt the contents of the original object.
        
        state_subs -= reduce_state
        
        state_subs *= -1
    
        state_subs.subs(reduce_state, state_subs)
        print state_subs, ' state_subs'

        td_rates = {}  # declare an empty dictionary.


        for state in self.kinetic_states:
            # populate the dictionary with empty 2D lists.
            td_rates[state] = ([], [])

     

        for reaction in self.reactions.itervalues():
     
            # reaction[0] ==from_state, reaction[1]==to_state
            td_rates[reaction.from_state][0].append(reaction.forward_rate)
            td_rates[reaction.from_state][1].append((reaction.reverse_rate,
                                                     reaction.to_state))
            td_rates[reaction.to_state][0].append(reaction.reverse_rate)
            td_rates[reaction.to_state][1].append((reaction.forward_rate,
                                                   reaction.from_state))

        time_derivatives = []
        for state_name, (outgoing_rates, incoming_rates) in td_rates.iteritems():
            td = TimeDerivative(dependent_variable=state_name, rhs='0')
            if (state_name not in (c.state for c in constraints)):
                for rate in outgoing_rates:
                    outcoming_state = self.kinetic_states[state_name]
                    td -= rate * outcoming_state
 
                    #print type(td), type(rate), type(outcoming_state)
                    #state_subs
                for rate, incoming_state_name in incoming_rates:
                    incoming_state = self.kinetic_states[incoming_state_name]
                    td += rate * incoming_state
          
                td.rhs=td.rhs.subs(reduce_state, state_subs)
                time_derivatives.append(td)


        # Construct base class members and pass to base class __init__
        for reaction in reactions:
            aliases.append(reaction.forward_rate)
            aliases.append(reaction.reverse_rate)

        regimes = [Regime(name="default", time_derivatives=time_derivatives)]

        state_variables = [StateVariable(name=ks.name, dimension=dimensionless)
                           for ks in self.kinetic_states.itervalues()
                           if ks.name not in (
                               c.state for c in self.constraints.itervalues())]
        
        
        super(KineticDynamicsBlock, self).__init__(
            regimes=regimes, aliases=aliases, state_variables=state_variables,
            constants=constants)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_dynamicsblock(self, **kwargs)

    def __repr__(self):
        return ('DynamicsBlock({} regimes, {} aliases, {} state_variables, '
                '{} reactions, kinetic_states {}, constraints {})'
                .format(len(list(self.regimes)), len(list(self.aliases)),
                        len(list(self.state_variables)),
                        len(list(self.reactions)),
                        len(list(self.kinetic_states)),
                        len(list(self.constraints))))


class Constraint(Expression, BaseALObject):

    defining_attributes = ('_state', '_rhs')
    #defining_attributes = ('_constraint')
    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    #constructor for making Constraint object.
    def __init__(self, expr, state):
        BaseALObject.__init__(self)
        Expression.__init__(self, expr)
        self._state = state

    @property
    def state(self):
        return self._state


class ReactionRate(Alias):

    def __init__(self, expr):
        self._rhs = expr
        self._reaction = None

    def set_reaction(self, reaction):
        if self._reaction is not None:
            raise NineMLRuntimeError(
                "Rate '{}' already belongs to another reaction block"
                .format(repr(self)))
        self._reaction = reaction

    @property
    def lhs(self):
        return self.name
#
# New Class, Constraint Inherits from Alias, which inherits from BaseAL.
#


class Reaction(BaseALObject):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('_from_state',' _to_state', 'from_', 'to',
                           'ForwardRate', 'ReverseRate')

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    def __init__(self, from_state, to_state, forward_rate, reverse_rate):

        """StateVariable Constructor

        :param name:  The name of the state variable.
        """

        self._from_state = from_state
        self._to_state = to_state
        self._forward_rate = forward_rate
        self._reverse_rate = reverse_rate

        #Reaction extends the BaseALObject 
        self._forward_rate.set_reaction(self)
        self._reverse_rate.set_reaction(self)

    @property
    def name(self):
        return (('reaction__from_{}_to{}').format(self._from_state, self._to_state ))
        #return (('__from_{}_to{}').format(self.from_state, self.to_state ))

    @property
    def from_state(self):
        return self._from_state

    @property
    def to_state(self):
        return self._to_state

    @property
    def forward_rate(self):
        return self._forward_rate

    @property
    def reverse_rate(self):
        return self._reverse_rate

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("Reaction(from={}, to={})"
                .format(self.from_state, self.to_state))


class KineticState(BaseALObject, ExpressionSymbol):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('name', 'dimension')

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    def __init__(self, name, dimension=None):
        """StateVariable Constructor

        :param name:  The name of the state variable.
        """
        self._name = name.strip()
        self._dimension = dimension if dimension is not None else dimensionless
        ensure_valid_identifier(self._name)

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("StateVariable({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))

    def _sympy_(self):
        return sympy.Symbol(self.name)


class ForwardRate(ReactionRate):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """
    defining_attributes = ('_rhs')

    element_name = 'ForwardRate'

    @property
    def name(self):
        return 'ReactionRate__from{}_to{}'.format(self._reaction.from_state,
                                                  self._reaction.to_state)


class ReverseRate(ReactionRate):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """
    defining_attributes = ('_rhs')

    element_name = 'ReverseRate'
        
    @property
    def name(self):
        return 'ReactionRate__from{}_to{}'.format(self._reaction.to_state,
                                                  self._reaction.from_state)


class KineticDynamicsClassXMLLoader(DynamicsClassXMLLoader):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_componentclass(self, element):

        blocks = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                  'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                  'KineticDynamics')

        subnodes = self._load_blocks(element, blocks=blocks)
        kineticsblock = expect_single(subnodes["KineticDynamics"])

        return KineticDynamicsClass(
            name=element.get('name'),
            parameters=subnodes["Parameter"],
            analog_ports=chain(subnodes["AnalogSendPort"],
                               subnodes["AnalogReceivePort"],
                               subnodes["AnalogReducePort"]),
            event_ports=chain(subnodes["EventSendPort"],
                              subnodes["EventReceivePort"]),
            kineticsblock=kineticsblock)

    @read_annotations
    def load_kineticsblock(self, element):

        subblocks = ('KineticState', 'Reaction', 'Constraint',
                     'ForwardRate', 'ReverseRate','Alias')
        subnodes = self._load_blocks(element, blocks=subblocks)

        return KineticDynamicsBlock(
            kinetic_states=subnodes["KineticState"],
            aliases=subnodes["Alias"],
            reactions=subnodes["Reaction"],
            constraints=subnodes["Constraint"],
        )

    @read_annotations
    #user lower case.
    def load_KineticState(self, element):
        name = element.get("name")
        dimension = self.document[element.get('dimension')]
        return KineticState(name=name, dimension=dimension)

    @read_annotations
    def load_Constraint(self, element):
        #what to do when there are two elements, one Alias/MathInline, and the other 
        #state
        state = element.get("state")
        expr = self.load_single_internmaths_block(element)

        return Constraint(expr,state)

    @read_annotations
    def load_Reaction(self, element):
        from_state = element.get("from")
        to_state = element.get("to")
        subblocks = ('ForwardRate', 'ReverseRate')
        subnodes = self._load_blocks(element, blocks=subblocks)
        #Gets the rate from the XML tag of the same name.
        forward_rate = expect_single(subnodes['ForwardRate'])
        reverse_rate = expect_single(subnodes['ReverseRate'])
        return Reaction(from_state, to_state, forward_rate, reverse_rate) 

    @read_annotations 
    def load_forwardrate(self, element):
        expr = self.load_single_internmaths_block(element)
        return ForwardRate(expr)

    @read_annotations
    def load_reverserate(self, element):
        expr = self.load_single_internmaths_block(element)
        return ReverseRate(expr)

    tag_to_loader = {                 
        "KineticDynamics": load_kineticsblock,                
        "Constraint": load_Constraint,
        "Reaction": load_Reaction,
        "KineticState": load_KineticState,
        "AnalogReceivePort": DynamicsClassXMLLoader.load_analogreceiveport,
        "AnalogSendPort": DynamicsClassXMLLoader.load_analogsendport,    
        "AnalogReducePort": DynamicsClassXMLLoader.load_analogreduceport,
        #"ComponentClass": load_componentclass,

        #sub blocks
        "ForwardRate": load_forwardrate,
        "ReverseRate": load_reverserate,

    }
