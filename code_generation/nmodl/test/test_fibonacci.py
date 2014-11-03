"""
Test of a mechanism that generates spikes at times given by the Fibonacci sequence (in milliseconds).

This is useless from a neuroscience perspective, but makes a nice test.

"""

from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort)
from util import TestFixture


model = ComponentClass(
    name="Fibonacci",
    regimes=[
        Regime(
            name="default",
            transitions=On("t > t_next",
                           do=["t_next = a + b",
                               "a = b",
                               "b = t_next",
                               OutputEvent('spikeOutput')]))
    ],
)

parameters = {}
initial_values = {
    'a': 1,  #0,
    'b': 1,
    't_next': 1
}
expected_output = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


def test_fibonacci(with_figure=False):
    test = TestFixture(model, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_fibonacci.png")
    assert success


if __name__ == "__main__":
    test_fibonacci(with_figure=True)
