"""
A framework for functional tests of nineml2nmodl.

Each test takes a NineML abstraction layer dynamics component,
generates an NMODL file, compiles it, runs a simulation with NEURON
and compares the results to the expected values.

"""

import os
import shutil
from StringIO import StringIO
from subprocess import check_call, STDOUT, CalledProcessError

from neuron import h, load_mechanisms
import numpy
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

from nineml.abstraction_layer.dynamics.component_modifiers import ComponentModifier
from nineml.abstraction_layer.dynamics.flattening import flatten
from nineml2nmodl import write_nmodl, write_nmodldirect


BUILD_DIR = "build/"


def clear_and_recreate_dir(dir_name):
    print '  -- Clearing the build_dir: %s' % dir_name
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    os.makedirs(dir_name)


def compile_nmodl(dir_name):
    cwd = os.getcwd()
    os.chdir(dir_name)
    print 'Compiling nmodl in', os.getcwd()
    stdout = open("stdout.txt", "wb")
    try:
        check_call('nrnivmodl', stdout=stdout, stderr=STDOUT)
    except CalledProcessError:
        stdout.close()
        stdout = open("stdout.txt", "rb")
        raise Exception("nrnivmodl error.\n    %s" % "    ".join(stdout.readlines()))
    finally:
        os.chdir(cwd)
        stdout.close()


def write_and_compile_nmodl(component):
    build_dir = os.path.join(BUILD_DIR, component.name.replace('-', '_'))
    clear_and_recreate_dir(build_dir)
    if not component.is_flat():
        component = flatten(component)
    ComponentModifier.close_all_reduce_ports(component=component)
    print '  -- Writing Component to .mod'
    modfilename = os.path.join(build_dir, component.name + '.mod').replace('-', '_')
    write_nmodldirect(component=component, mod_filename=modfilename, weight_variables={})
    compile_nmodl(build_dir)
    return build_dir


def configure(absolute_tolerance):
    cvode = h.CVode()
    cvode.active(1)
    cvode.condition_order(2)
    cvode.atol(absolute_tolerance)


def run(duration):
    h.finitialize()
    while h.t < duration:
        h.fadvance()


class _Initializer(object):
    """
    Manage initialization of NEURON cells. Rather than create an
    `FInializeHandler` instance for each cell that needs to initialize itself,
    we create a single instance, and use an instance of this class to maintain
    a list of cells that need to be initialized.

    Public methods:
        register()
    """

    def __init__(self):
        """
        Create an `FinitializeHandler` object in Hoc, which will call the
        `_initialize()` method when NEURON is initialized.
        """
        h('objref initializer')
        h.initializer = self
        self.fih = h.FInitializeHandler(1, "initializer._initialize()")
        self.cell_list = []

    def register(self, cell):
        """
        Add to the list of cells to be initialized. Cell objects must have an
        `initialize()` method.
        """
        assert hasattr(cell, "initialize")
        self.cell_list.append(cell)

    def _initialize(self):
        """Call `initialize()` for all registered cell objects."""
        for cell in self.cell_list:
            cell.initialize()
initializer = _Initializer()
del _Initializer  # make sure only one instance exists


class TestFixture(object):

    def __init__(self, component, parameters, initial_values, expected_spike_times, run_time):
        configure(1e-6)
        self.component = component
        build_dir = write_and_compile_nmodl(component)
        load_mechanisms(build_dir)
        self.name = component.name
        self.section = h.Section()
        self.cell = getattr(h, self.name)(0.5, sec=self.section)
        for param, value in parameters.items():
            setattr(self.cell, param, value)
        self.initial_values = initial_values
        initializer.register(self)
        self.setup_recording()
        self.expected_spike_times = numpy.array(expected_spike_times)
        self.run_time = run_time

    def initialize(self):
        #print "Initialising %s (time = %g)" % (self.name, h.t)
        for variable, value in self.initial_values.items():
            setattr(self.cell, variable, value)

    def setup_recording(self):
        self.Vm = h.Vector()
        self.times = h.Vector()
        self.Vm.record(self.cell._ref_V)
        self.times.record(h._ref_t)

        self.spike_times = h.Vector()
        self.source = h.NetCon(self.cell, None)
        self.source.record(self.spike_times)

    def run(self):
        run(self.run_time)
        return self.success

    def plot(self, filename):
        plt.clf()
        plt.plot(self.times, self.Vm, 'bo-')
        plt.savefig(filename)

    def calculate_errors(self):
        spike_times = numpy.array(self.spike_times)
        if spike_times.shape != self.expected_spike_times.shape:
            errors = "Different spike counts: actual: %d, expected %d" % (spike_times.size, self.expected_spike_times.size)
        else:
            errors = (spike_times - self.expected_spike_times)/self.expected_spike_times
        print("\nExpected spike times: %s\nActual spike times: %s" % (self.expected_spike_times, spike_times))
        return errors

    @property
    def success(self):
        errors = self.calculate_errors()
        if isinstance(errors, basestring):  # error message
            success = False
        else:
            success = (errors < 0.001).all()
        return success
