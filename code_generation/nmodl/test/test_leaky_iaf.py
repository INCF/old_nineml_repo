# encoding: utf-8
"""
A test of injecting current into an integrate and fire neuron.

The expected spike times can be calculated exactly.

If run directly, the script will produce a figure.
If run via nose, it will not.
"""

import numpy
from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort)
from util import TestFixture


component = ComponentClass(
    "LeakyIAF",
    regimes=[
        Regime(
            name="subthreshold_regime",
            time_derivatives=["dV/dt = (-gL*(V-vL) + I)/C", ],
            transitions=[On("V> theta",
                            do=["t_spike = t", "V = V_reset",
                                OutputEvent('spikeoutput')],
                            to="refractory_regime")]),
        Regime(
            name="refractory_regime",
            transitions=[On("t >= t_spike + t_ref",
                            to='subthreshold_regime')])
    ],
    analog_ports=[SendPort("V")]
)


parameters = p = {
    'C': 1,          # nF
    'vL': -65,       # mV
    'I': 0.5,        # nA
    'V_reset': -70,  # mV
    'theta': -50,    # mV
    't_ref': 5,      # ms
    'gL': 0.01,      # µS
}
initial_values = {'V': -65, 't_spike': -1e9}


def time_to_spike(v_start):
    tau_m = p['C']/p['gL']
    x = p['vL'] + p['I']/p['gL']
    return tau_m*numpy.log((v_start - x)/(p['theta'] - x))
spike1 = time_to_spike(initial_values['V'])
spike2 = spike1 + p['t_ref'] + time_to_spike(p['V_reset'])
expected_output = numpy.array([spike1, spike2])


def test_leaky_iaf(with_figure=False):
    test = TestFixture(component, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_leaky_iaf.png")
    assert success
    #print zip(test.times, test.Vm)


if __name__ == "__main__":
    test_leaky_iaf(with_figure=True)
