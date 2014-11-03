#!/usr/bin/python
"""
Iterates over all the testable components found in the Python nineml distribution,
and checks that they compile successfully.
"""


from nineml.abstraction_layer.dynamics.testing_utils import TestableComponent
from util import write_and_compile_nmodl


def test_generator():
    testable_components = [TestableComponent(source_file)
                           for source_file in TestableComponent.list_available()]
    nrn_components = [tc() for tc in testable_components]  #  if (tc.has_metadata() and tc.metadata.is_neuron_model)]
    for tc in nrn_components:
        yield write_and_compile_nmodl, tc




