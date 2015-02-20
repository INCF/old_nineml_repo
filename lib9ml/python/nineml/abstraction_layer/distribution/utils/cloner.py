"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentCloner)
from .visitors import DistributionActionVisitor


class DistributionExpandPortDefinition(DistributionActionVisitor,
                                       ComponentExpandPortDefinition):

    pass


class DistributionExpandAliasDefinition(DistributionActionVisitor,
                                        ComponentExpandAliasDefinition):

    """
    An action-class that walks over a componentclass, and expands an alias in
    Aliases
    """

    pass


class DistributionCloner(ComponentCloner):

    def visit_componentclass(self, componentclass, **kwargs):
        super(DistributionCloner, self).visit_componentclass(componentclass)
        ccn = componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters],
            distributionblock=(
                componentclass.distribution.accept_visitor(self, **kwargs)
                if componentclass.distribution else None))
        return ccn

    def visit_distributionblock(self, distributionblock, **kwargs):
        return distributionblock.__class__(
            aliases=[
                a.accept_visitor(self, **kwargs)
                for a in distributionblock.aliases])
