from nineml.abstraction_layer.dynamics import DynamicsBlock

from nineml.abstraction_layer import BaseALObject
from nineml.abstraction_layer.expressions.base import Alias
class KineticDynamicsBlock(DynamicsBlock):

    """
    An object, which encapsulates a component's regimes, transitions,
    and state variables
    """

    defining_attributes = ('_regimes', '_aliases', '_state_variables')

    def __init__(self, kinetic_state=None, reactions=None, constraint=None,
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
        print aliases
        #regimes = normalise_parameter_as_list(regimes)
        #state_variables = normalise_parameter_as_list(state_variables)
        #constants = normalise_parameter_as_list(constants)
        #piecewises = normalise_parameter_as_list(piecewises)
        #randomvariables = normalise_parameter_as_list(randomvariables)

        kinetic_state = normalise_parameter_as_list(kinetic_state)
        reactions = normalise_parameter_as_list(reactions)
        constraint = normalise_parameter_as_list(constraint)

        # Load the KineticStates  as objects or strings:
        sv_types = (basestring, kinetic_state)
        sv_td = filter_discrete_types(state_variables, sv_types)
        sv_from_strings = [kinetic_state(o, dimension=None)
                           for o in sv_td[basestring]]
        state_variables = sv_td[kinetic_state] + sv_from_strings

 

        # Kinetics specific members
        self._reactions = dict((r.name, r) for r in reactions)
        self._kinetic_state = dict((a.lhs, a) for a in kinetic_state)
        self._constraint = dict((s.name, s) for s in constraint)
        
        # DynamicsBlock base class members
        self._constants = dict((c.name, c) for c in constants)
        self._aliases = dict((a.lhs, a) for a in aliases)
        
        for reaction in reactions:
            self._aliases[reaction.name + '_forward'] = reaction.forward_rate
            self._aliases[reaction.name + '_reverse'] = reaction.reverse_rate
   
        
        

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




class Reaction(BaseALObject):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('to', 'from', 'ForwardRate', 'ReverseRate')

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    def __init__(self, name, dimension=None):
        """StateVariable Constructor

        :param name:  The name of the state variable.
        """
        self._to = name.strip()
        self._from = dimension if dimension is not None else dimensionless
        ensure_valid_identifier(self._name)

    @property
    def name(self):
        print reaction__
        #return ('reaction__from{}_to{}'.format(reaction.from, reaction.to))




    @property
    #def to(self):
        #return self._to

    @property
    #def from(self):
        #return self._from

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

class ForwardRate(Alias):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """
    element_name = 'ForwardRate'


class ReverseRate(Alias):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """
    element_name = 'ForwardRate'

