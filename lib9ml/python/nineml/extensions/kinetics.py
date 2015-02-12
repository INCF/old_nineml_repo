from nineml.abstraction_layer.dynamics import DynamicsBlock

from nineml.abstraction_layer import BaseALObject
from nineml.abstraction_layer.expressions.base import Alias

from nineml.abstraction_layer.dynamics.utils.xml import DynamicsClassXMLLoader, DynamicsClassXMLWriter


from nineml import annotations 
from nineml import utils
from nineml.annotations import read_annotations
from nineml.abstraction_layer.units import dimensionless
from nineml.utils import ensure_valid_identifier, expect_single
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import normalise_parameter_as_list
from nineml.utils import filter_discrete_types

class KineticDynamicsBlock(DynamicsBlock):

    """
    An object, which encapsulates a component's regimes, transitions,
    and state variables
    """

    defining_attributes = ('_regimes', '_aliases', '_state_variables')

    def __init__(self, kinetic_state=None, reactions=None, constraints=None,
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
        #print aliases
        #regimes = normalise_parameter_as_list(regimes)
        #state_variables = normalise_parameter_as_list(state_variables)
        #constants = normalise_parameter_as_list(constants)
        #piecewises = normalise_parameter_as_list(piecewises)
        #randomvariables = normalise_parameter_as_list(randomvariables)

        kinetic_state = normalise_parameter_as_list(kinetic_state)
        reactions = normalise_parameter_as_list(reactions)
        constraint = normalise_parameter_as_list(constraints)

        # Load the KineticStates  as objects or strings:
        sv_types = (basestring, kinetic_state)
        #sv_td = filter_discrete_types(kinetic_state, sv_types)
        #sv_from_strings = [kinetic_state(o, dimension=None)
        #                   for o in sv_td[basestring]]
        #state_variables = sv_td[kinetic_state] + sv_from_strings

 

        # Kinetics specific members
        self._reactions = dict(((r.from_state, r.to_state), r)
                               for r in reactions)
        for reaction in reactions:
           self._aliases[reaction.name + '_forward'] = reaction.forward_rate
           self._aliases[reaction.name + '_reverse'] = reaction.reverse_rate
       
        
        #self._reactions = dict(((r.from_state.name, r.to_state.name), r)
        #                       for r in reactions)
        self._kinetic_state = dict((a.name, a) for a in kinetic_state)
        self._constraints = set(constraints)
        
        # DynamicsBlock base class members
        #self._constants = dict((c.name, c) for c in constants)
        #self._aliases = dict((a.lhs, a) for a in aliases)
        
        
        
        

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_dynamicsblock(self, **kwargs)

    def __repr__(self):
        return ('DynamicsBlock({} regimes, {} aliases, {} state-variables, {} reactions, kinetic_state {}, constraint {})'
                .format(len(list(self.regimes)), len(list(self.aliases)),
                        len(list(self.state_variables)),
                        len(list(self.reactions)),
                        len(list(self.kinetic_state)),
                        len(list(self.constraint)),
                        ))

    @property
    def reactions(self):
        return self._reactions.itervalues()

    @property
    def reactions_map(self):
        return self._reactions
    
    @property
    def kinetic_state(self):
        return self._kinetic_state.itervalues()

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
        
    def lhs(self):
        return '{}__from{}_to{}_{}'.format(self.element_name,
                                          self._reaction.to_state,
                                          self._reaction.from_state)
        
    
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
        
        
   
        
        
# 
#     def set_constraint(self, constraint):
#         if self._reaction is not None:
#             raise NineMLRuntimeError(
#                 "Constraint '{}' already belongs to another reaction block"
#                 .format(repr(self)))
#         self._constraint = constraint

        
    


class Reaction(BaseALObject):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('from_', 'to', 'ForwardRate', 'ReverseRate')

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
        return (('reaction__from_{}_to{}').format(reaction._from_, reaction._to ))



    @property
    def from_state(self):
        return self._from_state

    @property
    def to_state(self):
        return self._to_state

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
    def load_kineticsblock(self, element):
        #,kinetic_state=None, reactions=None, constraint
#         subblocks = ('Regime', 'Alias', 'StateVariable', 'Constant',
#                      'Piecewise', 'RandomVariable','KineticState', 
#                      'Reaction', 'Constraint')
#         subnodes = self._load_blocks(element, blocks=subblocks)

        subblocks = ('KineticState', 'Reaction', 'Constraint',
                     'ForwardRate', 'ReverseRate','Alias')
        subnodes = self._load_blocks(element, blocks=subblocks)

 
        return KineticDynamicsBlock(
            kinetic_state=subnodes["KineticState"],
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
        
        #constraint is more like a Alias than a time derivative currently
        #Dummy return type replace with a real constraint class, after I have made one.
        return Constraint(expr)
        #return TimeDerivative(dependent_variable=variable,
        #                      rhs=expr)
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
        return ReactionRate(ForwardRate)
     
        


    @read_annotations
    def load_reverserate(self, element):
        return ReactionRate(ReverseRate)

 
 
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

