# encoding: utf-8
"""
A test of injecting current into a Hodgkin-Huxley neuron.

TODO: test against the built-in hh model
"""

from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort)
from util import TestFixture


component = ComponentClass(
    "HodgkinHuxley",
    aliases=[
        "q10 := 3.0**((celsius - 6.3)/10.0)",  # temperature correction factor
        "alpha_m := -0.1*(V+40.0)/(exp(-(V+40.0)/10.0) - 1.0)",  # m
        "beta_m := 4.0*exp(-(V+65.0)/18.0)",
        "mtau := 1/(q10*(alpha_m + beta_m))",
        "minf := alpha_m/(alpha_m + beta_m)",
        "alpha_h := 0.07*exp(-(V+65.0)/20.0)",                   # h
        "beta_h := 1.0/(exp(-(V+35)/10.0) + 1.0)",
        "htau := 1.0/(q10*(alpha_h + beta_h))",
        "hinf := alpha_h/(alpha_h + beta_h)",
        "alpha_n := -0.01*(V+55.0)/(exp(-(V+55.0)/10.0) - 1.0)",  # n
        "beta_n := 0.125*exp(-(V+65.0)/80.0)",
        "ntau := 1.0/(q10*(alpha_n + beta_n))",
        "ninf := alpha_n/(alpha_n + beta_n)",
        "gna := gnabar*m*m*m*h",
        "gk := gkbar*n*n*n*n",
        "ina := gna*(ena - V)",
        "ik := gk*(ek - V)",
        "il := gl*(el - V )"],
    regimes=[
        Regime(
            name="main",
            time_derivatives=[
                "dn/dt = (ninf-n)/ntau",
                "dm/dt = (minf-m)/mtau",
                "dh/dt = (hinf-h)/htau",
                "dV/dt = (ina + ik + il + I)/C"],
            transitions=On("V > theta", do=OutputEvent('spikeoutput')))],
    analog_ports=[SendPort("V")],
    parameters=['el', 'C', 'ek', 'ena', 'gkbar', 'gnabar', 'theta',
                'gl', 'celsius', 'I']

)

parameters = p = {
    'I': 0.1,        # nA
    'C': 1.0e-3,     # nF
    'gnabar': 0.12,  # µS
    'gkbar': 0.036,
    'gl': 0.0003,
    'ena': 50.0,
    'ek': -77.0,
    'el': -54.3,
    'celsius': 6.3,
    'theta': -20.0
}
initial_values = {
    'V': p['el'],
    'm': 0.1694,
    'h': 0.2446,
    'n': 0.4863
}
expected_output = [0.52928012, 7.91076037, 14.89711766, 21.79792683,
                   28.6527109, 35.5109495 ]  # no idea if these are correct,
                                             # should really test against
                                             # built-in hh mechanism


def test_hh(with_figure=False):
    test = TestFixture(component, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_HH.png")
    assert success


if __name__ == "__main__":
    test_hh(with_figure=True)
