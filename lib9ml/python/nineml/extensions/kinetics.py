from nineml.abstraction_layer.dynamics import DynamicsBlock, regimes
from nineml.abstraction_layer import BaseALObject

from nineml.abstraction_layer.expressions import Alias

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
from nineml.abstraction_layer.dynamics.regimes import TimeDerivative, Regime
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
                           '_reactions', '_constraints','_main_block'
                           )

    def __init__(self, name, 
                 parameters=None, analog_ports=[],
                 event_ports=[], aliases=None, constants=None,
                 kinetic_states=None, reactions=None, constraints=None,
                 kineticsblock=None, main_block=None):
        self._main_block = kineticsblock
        #self._main_block = reactions
         
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


        td_rates = {} #declare an empty dictionary.
        
        for state in self.kinetic_states:
            td_rates[state.name] = ([],[])  #populate the dictionary with empty 2D lists.
        
        
        for reaction in self.reactions:


            td_rates[reaction.from_state][0].append(reaction.forward_rate)
            td_rates[reaction.from_state][1].append((reaction.reverse_rate, reaction.to_state))
  
            td_rates[reaction.to_state][0].append(reaction.reverse_rate)
            td_rates[reaction.to_state][1].append((reaction.forward_rate, reaction.from_state))
           
            #Delete the below comments:
            #td_rates[reaction.to_state][0].append(reaction.reverse_rate)
            #td_rates[reaction.from_state][0].append(reaction.forward_rate)
            #td_rates[reaction.from_state][1].append((reaction.reverse_rate, reaction.to_state))

        time_derivatives = []
        for state_name, (outgoing_rates, incoming_rates) in td_rates.iteritems():
            
            td = TimeDerivative(dependent_variable=state_name, rhs='0')
            #state = self.kinetic_states_map[state_name]
      
            for rate in outgoing_rates:
                outcoming_state = self.kinetic_states_map[state_name]
                td -= rate * outcoming_state._sympy_()
                
                
            for rate, incoming_state_name in incoming_rates:
                incoming_state = self.kinetic_states_map[incoming_state_name]
        
                td += rate * incoming_state._sympy_()
            time_derivatives.append(td)
        regime = Regime(name="default", time_derivatives=time_derivatives)    
            

            #state = self.kinetic_states[state_name]
            #state = kinetic_states[state_name]
            #state = self.kineticsdynamicsblock.kinetic_states[state_name]
        for td in regime.time_derivatives:
            print td       

        super(KineticDynamicsClass, self).__init__(name=name, parameters=parameters, event_ports=event_ports,
            analog_ports=analog_ports, dynamicsblock=kineticsblock, regimes=regime)
    
    @property
    def kineticsdynamicsblock(self):
        return self._main_block
    
    @property
    def reactions(self):
        return self.kineticsdynamicsblock.reactions
   
   
    
    @property
    def kinetic_states_map(self):
        return self.kineticsdynamicsblock._kinetic_states
   
    @property
    def kinetic_states(self):
        return self.kineticsdynamicsblock.kinetic_states
#   @property
#    def constraints(self):
#        return self.kineticsdynamicsblock.constraints
    





    
        

class KineticDynamicsBlock(DynamicsBlock):

    """
    An object, which encapsulates a component's regimes, transitions,
    and state variables
    """

    defining_attributes = ('_regimes', '_aliases', '_state_variables', '_constraints')

    def __init__(self, kinetic_states=None, reactions=None, constraints=None,
                 constants=None, aliases=None): #Note could have kinetic aliases instead of aliases 
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
        constraint = normalise_parameter_as_list(constraints)

        # Load the KineticStates  as objects or strings:
        sv_types = (basestring, kinetic_states)

 

        # Kinetics specific members
        self._reactions = dict(((r.from_state, r.to_state), r)
                               for r in reactions)
        
        #self._reactions = dict(((r.from_state.name, r.to_state.name), r)
        #                       for r in reactions)
        self._aliases = {}
        for reaction in reactions:
           self._aliases[reaction.name + '_forward'] = reaction.forward_rate
           self._aliases[reaction.name + '_reverse'] = reaction.reverse_rate
       
        
        
        #Above was commented out.
        self._kinetic_states = dict((a.name, a) for a in kinetic_states)
               
        self._constraints = set(constraint)
        
        # DynamicsBlock base class members
        #self._constants = dict((c.name, c) for c in constants)
        #self._aliases = dict((a.lhs, a) for a in aliases)
        
        
        
        

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_dynamicsblock(self, **kwargs)

    def __repr__(self):
        return ('DynamicsBlock({} regimes, {} aliases, {} state-variables, {} reactions, kinetic_states {}, constraint {})'
                .format(len(list(self.regimes)), len(list(self.aliases)),
                        len(list(self.state_variables)),
                        len(list(self.reactions)),
                        len(list(self.kinetic_states)),
                        len(list(self.constraint)),
                        ))

    @property
    def reactions(self):
        return self._reactions.itervalues()

    @property
    def reactions_map(self):
        return self._reactions
    
    @property
    def kinetic_states(self):
        return self._kinetic_states.itervalues()


    
    @property
    def kinetic_states_map(self):
        return self._kinetic_states

    @property
    def constraint_map(self):
        return self._constraint
    
    @property
    def constraint(self):
        return self._constraint.itervalues()

    @property
    def alias(self):
        return self.alias.itervalues()


    @property
    def aliases_map(self):
        return self._aliases



class ReactionRate(Alias):
    
    def __init__(self, expr):
        self._lhs = expr
        self._reaction = None
        
    def set_reaction(self, reaction):
        if self._reaction is not None:
            raise NineMLRuntimeError(
                "Rate '{}' already belongs to another reaction block"
                .format(repr(self)))
        self._reaction = reaction
        
    @property
    def name(self):
        return '{}__from{}_to{}'.format(self.element_name,
                                           self._reaction.to_state,
                                           self._reaction.from_state)

    @property        
    def lhs(self):
        return self.name
#
# New Class, Constraint Inherits from Alias, which inherits from BaseAL.
#





class Constraint(Alias):

    defining_attributes = ('_constraint')

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    #constructor for making Constraint object.
    def __init__(self, expr):
        self._constraint = expr
        self._lhs = expr
        
        
   
        
        
        
    


class Reaction(BaseALObject):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('_from_state',' _to_state', 'from_', 'to', 'ForwardRate', 'ReverseRate')

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
        
        #set_reaction is a method that belongs to the class ReactionRate which extends
        #the class Alias, does Alias extend the BaseALObject?
        
        #Reaction extends the BaseALObject 
        self._forward_rate.set_reaction(self)
        self._reverse_rate.set_reaction(self)
        
    @property
    def name(self):
        #return (('reaction__from_{}_to{}').format(self._from_state, self._to_state ))
        return (('__from_{}_to{}').format(self.from_state, self.to_state ))
 
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


#  
#     @property
#     def from_state(self):
#         return self.from_state
#  
#     @property
#     def to_state(self):
#         return self.to_state

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("StateVariable({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))


class KineticState(BaseALObject):

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
    element_name = 'ForwardRate'


class ReverseRate(ReactionRate):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """
    element_name = 'ReverseRate'
    
    



    
    
        
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
        variable = element.get("variable")
        expr = self.load_single_internmaths_block(element)
        
        return Constraint(expr)
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
        



    #Dummy return type replace with a real constraint class, after I have made one.
    #return TimeDerivative(dependent_variable=variable,
    #                      rhs=rexpr) 
    @read_annotations 
    def load_forwardrate(self, element):
        return ForwardRate(element.text)


    @read_annotations
    def load_reverserate(self, element):
        return ReverseRate(element.text)

 
 
    tag_to_loader = {                 
        "KineticDynamics": load_kineticsblock,                
        "Constraint": load_Constraint,
        "Reaction": load_Reaction,
        "KineticState": load_KineticState,         
        #"ComponentClass": load_componentclass,

        
        #sub blocks
        "ForwardRate": load_forwardrate,
        "ReverseRate": load_reverserate,

    }

