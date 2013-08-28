import nineml
from . import biophysical_cells

extended_component_classes = { (biophysical_cells.BIO_CELL_NINEML +
                                biophysical_cells.ComponentClass.element_name):
                               biophysical_cells.ComponentClass}

def load_componentclass(element):
    try:
        ComponentClass = extended_component_classes[element.tag]
    except KeyError:
        raise Exception("Did not find registered extension for component class type '<{}>'"
                        .format(element.tag))
    return ComponentClass.from_xml(element)
