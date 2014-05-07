#!/usr/bin/python
"""

"""

import os
import sys
import shutil
from StringIO import StringIO
from subprocess import check_call, STDOUT, CalledProcessError

import nose

from nineml.abstraction_layer.component_modifiers import ComponentModifier
from nineml.abstraction_layer.flattening import flatten
from nineml.abstraction_layer.testing_utils import TestableComponent
from nineml2nmodl import write_nmodl, write_nmodldirect


BUILD_DIR = "build/"


def clear_and_recreate_dir(dir_name):
    print '  -- Clearing the build_dir: %s' % dir_name
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    os.mkdir(dir_name)


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


def test_generator():
    testable_components = [TestableComponent(source_file)
                       for source_file in TestableComponent.list_available()]
    nrn_components = [tc() for tc in testable_components] #  if (tc.has_metadata() and tc.metadata.is_neuron_model)]
    for tc in nrn_components:
        yield write_and_compile_nmodl, tc


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

