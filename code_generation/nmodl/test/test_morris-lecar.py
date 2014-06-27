# encoding: utf-8
"""
A test of injecting current into a Morris-Lecar neuron.
"""


from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort)
from util import TestFixture


component = ComponentClass(
    "MorrisLecar",
    regimes=[
        Regime(
            name="subthreshold_regime",
            transitions=[On("V > theta", do=OutputEvent('spikeoutput'))],
            time_derivatives=[
                "dV/dt = (g_l*(V_l - V) + I_ca + I_k + I)/C",
                "dW/dt = lambda_W*(W_inf - W)",
            ])],
    aliases=[
        "M_inf := 0.5*(1.0+tanh((V-V1)/V2))",
        "W_inf := 0.5*(1.0+tanh((V-V3)/V4))",
        "lambda_W := phi*cosh((V-V3)/(2.0*V4))",
        "I_ca := g_ca*M_inf*(V_ca-V)",
        "I_k := g_k*W*(V_k-V)"],
    analog_ports=[SendPort("V"), SendPort("W")]
)

parameters = {
    'C': 10,
    'V1': -1.2,
    'I': 100,
    'phi': 0.04,
    'V2': 18,
    'g_l': 2,
    'g_ca': 4.4,
    'V3': 2,
    'V4': 30,
    'g_k': 8,
    'theta': 20,
    'V_l': -60,
    'V_ca': 120,
    'V_k': -84,
}
initial_values = {
    'V': -65,
    'W': 0
}
expected_output = [8.19, 77.90]  # no idea if these are the correct values


def test_morris_lecar(with_figure=False):
    test = TestFixture(component, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_morris-lecar.png")
    assert success


if __name__ == "__main__":
    test_morris_lecar(with_figure=True)
