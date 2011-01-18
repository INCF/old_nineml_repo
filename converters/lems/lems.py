# -*- coding: utf-8 -*-
"""

Initial version of converter 9ML -> LEMS
Can be used to convert AL models in 9ml to LEMS to be executed with the LEMS interpreter

Based on scripts from Andrew Davison & Eilif Muller's libnineml

Author: Padraig Gleeson

"""

from lxml import etree
from lxml.builder import E
import os, sys


import nineml.user_layer as UL
import nineml.abstraction_layer as AL

LEMS_EL = "Lems"
DEFAULT_RUN="DefaultRun"
SIMULATION="Simulation"
DISPLAY="Display"
LINE="Line"


class LEMS():

  includes = []
  components = {}
  componentTypes = {}
  networks = {}
  description = "LEMS created with Python interface"
  
  def __init__(self, sim_name, dur, dt):
    self.sim_name = sim_name
    self.dur = float(dur)
    self.dt = float(dt)
    self.includes.append(Include("NeuroML2CoreTypes/Cells.xml"))
    self.includes.append(Include("NeuroML2CoreTypes/Networks.xml"))
    self.includes.append(Include("NeuroML2CoreTypes/Simulation.xml"))

  def add_network(self, network):
    self.networks[network.id] = network

  
  def to_xml(self):
    def_run = E(DEFAULT_RUN, component=self.sim_name)
    lems_xml = E(LEMS_EL, def_run)

    for include in self.includes:
        lems_xml.append(include.to_xml())

    for comp_type in self.componentTypes.keys():
        lems_xml.append(self.componentTypes[comp_type].to_xml())


    for comp in self.components.values():
        lems_xml.append(comp.to_xml())

    for net in self.networks.keys():
        lems_xml.append(self.networks[net].to_xml())

    net_to_sim = self.networks[self.networks.keys()[0]]

    simulation = E(SIMULATION, id=self.sim_name, length="%fms"%self.dur, step="%fms"%self.dt, target=net_to_sim.id)
    
    display = E(DISPLAY, id="d1", title=self.description, timeScale="1s")
    simulation.append(display)

    for pop_name in net_to_sim.populations.keys():
        pop = net_to_sim.populations[pop_name]
        line = E(LINE, id="l1", quantity=pop.id+"[0]/V", color="#0040FF", scale="1")
        display.append(line)


    lems_xml.append(simulation)

    return lems_xml

  def read_9ml(self, components_9ml, model):
      print "Reading elements from 9ML: "+model.name

      self.description = model.name

      for comp9 in components_9ml:
          print "  Adding component of type: %s"%comp9.name
          componentType = ComponentType(comp9.name)
          componentType.read_9ml(comp9)
          self.componentTypes[componentType.name] = componentType

      for component_name9 in model.components.keys():
          print "  Adding component_name9 %s in the LEMS object model"%component_name9
          component9 = model.components[component_name9]
          comp = Component(component9.definition.url, component9.name)

          for param_name9 in component9.parameters.keys():
              param9 = component9.parameters[param_name9]
              comp.parameter_values[param9.name] = str(param9.value)

          self.components[comp.id] = comp

      for group9 in model.groups.keys():
          print "  Adding group %s as a network in the LEMS object model"%group9
          network = Network(group9)
          self.networks[network.id] = network
          
          for pop9 in model.groups[group9].populations.values():
              print "  Adding population %s as a population in the LEMS object model"%pop9
              population = Population(pop9.name, pop9.prototype.name, pop9.number)
              network.add_population(population)
              
      print "Added all elements from 9ML..."
    

  def write(self, file): 
    
    
    etree.ElementTree(self.to_xml()).write(file, encoding="UTF-8",
                                     pretty_print=True, xml_declaration=True)


class BaseLEMS():

    type = "ComponentType"
    name = "???"

    def to_xml(self):
        element = E(self.type,
                    name=self.name)
        return element


class BaseNeuroML2():

    type = "component"
    id = "???"

    def to_xml(self):
        element = E(self.type,
                    id=self.id)
        return element


class Network(BaseNeuroML2):

    type = "network"
    populations = {}

    def __init__(self, id):
        self.id = id

    def add_population(self, pop):
        self.populations[pop.id] = pop

    def to_xml(self):
        element = E(self.type,
                    id=self.id)

        for p in self.populations.keys():
            pop = self.populations[p]
            print "Appending to XML of network: %s"%pop
            element.append(pop.to_xml())
            
        return element

class Population(BaseNeuroML2):

    type = "population"

    def __init__(self, id, component, size):
        self.id = id
        self.component = component
        self.size = size

    def __str__(self):
        return "LEMS/NeuroML 2 Population: %s"%(self.id)

    def to_xml(self):
        element = E(self.type,id=self.id, component = self.component, size=str(self.size))
                    
        return element



class Component(BaseNeuroML2):

    parameter_values = {}

    def __init__(self, type, id):
        self.type = type
        self.id = id

    def to_xml(self):
        attrs = {"id":self.id, "type":str(self.type)}

        for param_name in self.parameter_values:
            attrs[param_name] = self.parameter_values[param_name]+""

        sub_els = {}
        element = E("Component",*sub_els, **attrs)
                    
        return element


class ComponentType(BaseLEMS):

    type = "ComponentType"
    parameters = []
    constants = []

    def __init__(self, name):
        self.name = name
        self.behavior = Behavior()

    def to_xml(self):
        element = E(self.type,name=self.name)

        for param in self.parameters:
            element.append(param.to_xml())
            
        for const in self.constants:
            element.append(const.to_xml())


        for sv in self.behavior.state_variables:
            exposure = E("Exposure", name=sv.name, dimension="none")
            element.append(exposure)


        element.append(self.behavior.to_xml())
        return element
    
    def read_9ml(self, component9):

        timeScaleConst = "tscale"
        for param9 in component9.parameters:
            #param9 = component9.parameters[param_name9]
            print "Adding param: "+param9
            param = Parameter(param9)
            self.parameters.append(param)

        timeScale = Constant(timeScaleConst, "per_time", "1per_ms")
        self.constants.append(timeScale)
            
        for sv9 in component9.state_variables:
            self.behavior.state_variables.append(StateVariable(sv9))

        for regime9 in component9.regimes:
            print "  Adding info on regime "+regime9.name
            for ode9 in regime9.odes:
                self.behavior.time_derivatives.append(TimeDerivative(ode9.dependent_variable, timeScaleConst+" * ("+ode9.rhs+")"))

        for transition9 in component9.transitions:
            print "  Adding info on transition: "+transition9.name
            if transition9.to == transition9.from_:
                oc = OnCondition(transition9.condition)
                self.behavior.on_conditions.append(oc)
                for node9 in transition9.nodes:
                    print "     Adding info on node9: "+str(node9)
                    if isinstance(node9, AL.expressions.Assignment):
                        sa = StateAssignment(node9.to, node9.get_rhs())
                        oc.state_assignments.append(sa)
                    if isinstance(node9, AL.expressions.Inplace):
                        sa = StateAssignment(node9.to, node9.as_expr().replace("=", ""))
                        '''Quick & dirty fix for eqn'''
                        oc.state_assignments.append(sa)

            else:
                print "***  Multi regime transitions not implemented yet!!!  ***"

class Parameter(BaseLEMS):
    type = "Parameter"

    def __init__(self, name):
        self.name = name

    def to_xml(self):
        element = E(self.type,name=self.name, dimension="none")
        return element

    
class Parameter(BaseLEMS):
    type = "Parameter"

    def __init__(self, name):
        self.name = name

    def to_xml(self):
        element = E(self.type,name=self.name, dimension="none")
        return element


class Constant(BaseLEMS):
    type = "Constant"

    def __init__(self, name, dimension, value):
        self.name = name
        self.value = value
        self.dimension = dimension

    def to_xml(self):
        element = E(self.type,name=self.name, dimension=self.dimension, value=self.value)
        return element

class Include(BaseLEMS):
    type = "Include"

    def __init__(self, file):
        self.file = file

    def to_xml(self):
        element = E(self.type,file=self.file)
        return element


class Behavior(BaseLEMS):
    type = "Behavior"
    state_variables = []
    on_conditions = []
    time_derivatives = []

    def to_xml(self):
        element = E(self.type)
        for sv in self.state_variables:
            element.append(sv.to_xml())
        for oc in self.on_conditions:
            element.append(oc.to_xml())
        for td in self.time_derivatives:
            element.append(td.to_xml())
        return element

class OnCondition(BaseLEMS):
    type = "OnCondition"
    state_assignments = []

    def __init__(self, test):

        self.test = test.cond.replace(">", ".gt.").replace("<", ".lt.")

    def to_xml(self):
        element = E(self.type,test=self.test)
        for sa in self.state_assignments:
            element.append(sa.to_xml())
        return element


class StateVariable(BaseLEMS):
    type = "StateVariable"

    def __init__(self, name):
        self.name = name

    def to_xml(self):
        element = E(self.type,name=self.name, dimension="none", exposure=self.name)
        return element


class StateAssignment(BaseLEMS):
    type = "StateAssignment"

    def __init__(self, variable, value):
        self.variable = variable
        self.value = value

    def to_xml(self):
        element = E(self.type,variable=self.variable, value=self.value)
        return element

    

class TimeDerivative(BaseLEMS):
    type = "TimeDerivative"

    def __init__(self, variable, value):
        self.variable = variable
        self.value = value

    def to_xml(self):
        element = E(self.type,variable=self.variable, value=self.value)
        return element




if __name__ == "__main__":

    file_name = "TestLEMS.xml"
    file_al_9ml = "TestLEMS_AL.9ml"
    file_ul_9ml = "TestLEMS_UL.9ml"
    
    print "Testing LEMS export..."


    sys.path.append("../../lib9ml/python/examples/AL")
    import izhikevich

    print "Loaded abstraction layer definition: %s" % izhikevich.c1.name

    components_9ml = []
    components_9ml.append(izhikevich.c1)

    catalog = "../../catalog/"
    network = UL.Group("Network1")
    model = UL.Model("Simple 9ML example model (based on Izhikevich cell AL definition) to run on LEMS")
    model.add_group(network)

    al_definition_name = izhikevich.c1.name
    instance_name = "BurstingIzh"

    paramsBurst = UL.ParameterSet(a =(0.02, ""), b=(0.2, ""), c=(-50, ""), d=(2, ""), theta=(30, ""), Isyn=(15, ""))

    izh_burst_cell = UL.SpikingNodeType(instance_name, al_definition_name, paramsBurst)

    model.add_component(izh_burst_cell)

    unstructured = UL.Structure("Unstructured", catalog + "networkstructures/Unstructured.xml")

    cellPop = UL.Population("CellsA", 2, izh_burst_cell, UL.PositionList(structure=unstructured))

    network.add(cellPop)

    model.write(file_ul_9ml)

    lems_file = open(file_name, 'w')
    
    lems = LEMS("TestSim", 200, 0.01)

    lems.read_9ml(components_9ml, model)
    
    lems.write(lems_file)
    
    lems_file.close()
    
    print "Saved file to %s"%file_name

    run_in_lems = True

    if run_in_lems:
       os.system("java -jar lems-0.6.1.jar "+file_name)
    
    
    