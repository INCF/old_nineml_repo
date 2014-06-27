# encoding: utf-8
"""
A test of injecting current into an Izhikevich neuron.

"""

from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort)
from util import TestFixture

component = ComponentClass(
    "Izhikevich",
    regimes=[
        Regime(
            name="subthreshold_regime",
            time_derivatives=[
                "dV/dt = 0.04*V*V + 5*V + 140.0 - U + Isyn",
                "dU/dt = a*(b*V - U)"],
            transitions=[On("V > theta",
                            do=["V = c",
                                "U = U + d",
                                OutputEvent('spikeoutput')])])
    ],
    analog_ports=[SendPort("V")]
)

parameters = {
    'a': 0.02,
    'b': 0.2,
    'c': -50,
    'd': 2,
    'Isyn': 15,
    'theta': 0,
}
initial_values = {
    'V': -65,
    'U': 0.2 * -65
}
expected_output = [  # I have no idea if these values are correct
     2.11456013,   3.16223809,   4.28475028,   5.49598431,
     6.81459817,   8.26700621,   9.89299053,  11.75840739,
    13.98970098,  16.91909234,  50.10970927,  51.69737102,
    53.50838859,  55.65212206,  58.39190026,  63.44686492,
    97.1294706,   98.71712847]


def test_izhikevich(with_figure=False):
    test = TestFixture(component, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_izhikevich.png")
    assert success


if __name__ == "__main__":
    test_izhikevich(with_figure=True)
