from nineml.abstraction_layer.dynamics import Dynamics


class KineticDynamics(Dynamics):
    pass

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
    def to(self):
        return self._to

    @property
    def from(self):
        return self._from

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("StateVariable({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))



class CoupeledODE(BaseALObject):

    """
    A class representing a the coupled ODE that is implied by the Kinetic scheme.
    This pieces togethor all of the KineticStates, rate equations, and constraints
    in order to pass an argument to expression.ode.
    
    Assumes that tau values can be obtained from some sort of lookup table or dictionary.
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



class ReverseRate(ODE):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """

    def __init__(self, dependent_variable, rhs):
        """Time Derivative Constructor

            :param dependent_variable: A `string` containing a single symbol,
                which is the dependent_variable.
            :param rhs: A `string` containing the right-hand-side of the
                equation.


            For example, if our time derivative was:

            .. math::

                \\frac{dg}{dt} = \\frac{g}{gtau}

            Then this would be constructed as::

                TimeDerivative( dependent_variable='g', rhs='g/gtau' )

            Note that although initially the time variable
            (independent_variable) is ``t``, this can be changed using the
            methods: ``td.lhs_name_transform_inplace({'t':'T'} )`` for example.



            """
        ODE.__init__(self,
                     dependent_variable=dependent_variable,
                     independent_variable='t',
                     rhs=rhs)

    def __repr__(self):
        return "TimeDerivative( d%s/dt = %s )" % \
            (self.dependent_variable, self.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_timederivative(self, **kwargs)

    @classmethod
    def from_str(cls, time_derivative_string):
        """Creates an TimeDerivative object from a string"""
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r"""\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) """, re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
            raise NineMLRuntimeError(err)
        dependent_variable = match.groupdict()['dependent_var']
        rhs = match.groupdict()['rhs']
        return TimeDerivative(dependent_variable=dependent_variable, rhs=rhs)




class ForwardRate(ODE):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """

    def __init__(self, dependent_variable, rhs):
        """Time Derivative Constructor

            :param dependent_variable: A `string` containing a single symbol,
                which is the dependent_variable.
            :param rhs: A `string` containing the right-hand-side of the
                equation.


            For example, if our time derivative was:

            .. math::

                \\frac{dg}{dt} = \\frac{g}{gtau}

            Then this would be constructed as::

                TimeDerivative( dependent_variable='g', rhs='g/gtau' )

            Note that although initially the time variable
            (independent_variable) is ``t``, this can be changed using the
            methods: ``td.lhs_name_transform_inplace({'t':'T'} )`` for example.



            """
        ODE.__init__(self,
                     dependent_variable=dependent_variable,
                     independent_variable='t',
                     rhs=rhs)

    def __repr__(self):
        return "TimeDerivative( d%s/dt = %s )" % \
            (self.dependent_variable, self.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_timederivative(self, **kwargs)

    @classmethod
    def from_str(cls, time_derivative_string):
        """Creates an TimeDerivative object from a string"""
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r"""\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) """, re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
            raise NineMLRuntimeError(err)
        dependent_variable = match.groupdict()['dependent_var']
        rhs = match.groupdict()['rhs']
        return TimeDerivative(dependent_variable=dependent_variable, rhs=rhs)




class KineticTimeDerivative(ODE):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """

    def __init__(self, dependent_variable, rhs):
        """Time Derivative Constructor

            :param dependent_variable: A `string` containing a single symbol,
                which is the dependent_variable.
            :param rhs: A `string` containing the right-hand-side of the
                equation.


            For example, if our time derivative was:

            .. math::

                \\frac{dg}{dt} = \\frac{g}{gtau}

            Then this would be constructed as::

                TimeDerivative( dependent_variable='g', rhs='g/gtau' )

            Note that although initially the time variable
            (independent_variable) is ``t``, this can be changed using the
            methods: ``td.lhs_name_transform_inplace({'t':'T'} )`` for example.



            """
        ODE.__init__(self,
                     dependent_variable=dependent_variable,
                     independent_variable='t',
                     rhs=rhs)

    def __repr__(self):
        return "TimeDerivative( d%s/dt = %s )" % \
            (self.dependent_variable, self.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_timederivative(self, **kwargs)

    @classmethod
    def from_str(cls, time_derivative_string):
        """Creates an TimeDerivative object from a string"""
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r"""\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) """, re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
            raise NineMLRuntimeError(err)
        dependent_variable = match.groupdict()['dependent_var']
        rhs = match.groupdict()['rhs']
        return TimeDerivative(dependent_variable=dependent_variable, rhs=rhs)
