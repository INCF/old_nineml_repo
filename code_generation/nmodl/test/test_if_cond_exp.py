# encoding: utf-8
"""
Test of a composite leaky integrate-and-fire with conductance-based,
exponential synapses, like the IF_cond_exp standard cell model in PyNN.


"""
from neuron import h
from nineml.abstraction_layer.dynamics import (
    ComponentClass, Regime, On, OutputEvent, SendPort, RecvPort)
from util import TestFixture


component = ComponentClass(
    "IF_cond_exp",
    regimes=[
        Regime(
            name="sub_threshold_regime",
            time_derivatives=[
                "dV/dt = (v_rest - V)/tau_m + (gE*(e_rev_E - V) + gI*(e_rev_I - V) + i_offset)/cm",
                "dgE/dt = -gE/tau_syn_E",
                "dgI/dt = -gI/tau_syn_I", ],
            transitions=[On("V > v_thresh",
                            do=["t_spike = t",
                                "V = v_reset",
                                OutputEvent('spikeoutput')],
                            to="refractory_regime"),
                         On('excitatory', do="gE=gE+q"),
                         On('inhibitory', do="gI=gI+q")]),
        Regime(
            name="refractory_regime",
            time_derivatives=[
                "dgE/dt = -gE/tau_syn_E",
                "dgI/dt = -gI/tau_syn_I", ],
            transitions=[On("t >= t_spike + tau_refrac", to="sub_threshold_regime"),
                         On('excitatory', do="gE=gE+q"),
                         On('inhibitory', do="gI=gI+q")]),
    ],
    analog_ports=[SendPort("V"), SendPort("gE"), SendPort("gI"), RecvPort("q")]
)


SYN_TYPES = {  # argument 1 for net_receive
    'exc': 0,
    'inh': 1,
}


class TestIFCondExp(TestFixture):

    def __init__(self, component, parameters, initial_values, expected_spike_times, run_time):
        super(TestIFCondExp, self).__init__(component, parameters, initial_values, expected_spike_times, run_time)
        self.stimuli = {}
        self.add_stimulation("exc", 5, 10, 0.04)
        self.add_stimulation("inh", 17, 30, 0.05)

    def add_stimulation(self, label, start, interval, weight):
        stim = h.NetStim(0.5, sec=self.section)
        stim.noise = 0
        stim.start = start
        stim.interval = interval
        stim.number = 1e12
        delay = 1.0
        nc = h.NetCon(stim, self.cell, 0.5, delay, weight)
        assert nc.weight[0] == weight
        nc.weight[1] = SYN_TYPES[label]
        self.stimuli[label] = (stim, nc)


parameters = p = {
    'cm': 1,          # nF
    'v_rest': -65,    # mV
    'i_offset': 0.0,  # nA
    'v_reset': -70,   # mV
    'v_thresh': -60,  # mV
    'tau_refrac': 5,  # ms
    'tau_m': 10.0,    # ms
    'tau_syn_E': 2.0,
    'tau_syn_I': 5.0,
    'e_rev_E': 0,
    'e_rev_I': -70,
}
initial_values = {'V': -65, 'gE': 0, 'gI': 0, 't_spike': -1e9}
expected_output = [38.0033, 77.5482]


def test_if_cond_exp(with_figure=False):
    test = TestIFCondExp(component, parameters, initial_values, expected_output, 100.0)
    success = test.run()
    if with_figure:
        test.plot("test_if_cond_exp.png")
    assert success


if __name__ == '__main__':
    test_if_cond_exp(with_figure=True)
