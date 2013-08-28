import urllib
from itertools import chain
from lxml import etree
from lxml.builder import E
import nineml.extensions.morphology
import nineml.extensions.biophysics

biophysical_cells_namespace = 'http://www.nineml.org/BiophysicalCells'
BIO_CELL_NINEML = "{%s}" % biophysical_cells_namespace

def parse(url):
    """
    Read a NineML user-layer file and return a Model object.

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if not isinstance(url, file):
        f = urllib.urlopen(url)
        doc = etree.parse(f)
        f.close()
    else:
        doc = etree.parse(url)
    root = doc.getroot()
    comp_classes = {}
    for element in root.findall(BIO_CELL_NINEML + ComponentClass.element_name):
        comp_class = ComponentClass.from_xml(element)
        comp_classes[comp_class.name] = comp_class
    return comp_classes


class ComponentClass(object):

    element_name = 'ComponentClass'

    def __init__(self, name, parameters, mappings, morphology, biophysics):
        self.name = name
        self.parameters = parameters
        self.mappings = mappings
        self.morphology = morphology
        self.biophysics = biophysics

    def __repr__(self):
        return ("Morphology '{}' with {} segment(s) and {} mapping(s)"
                .format(self.name, len(self.parameters), len(self.mappings)))
        
    def check_consistency(self):
        pass # Not implemented yet

    def to_xml(self):
        return E(self.element_name,
                 E(nineml.extensions.morphology.Morphology.element_name, self.morphology.to_xml()),
                 E(nineml.extensions.biophysics.BiophysicsModel.element_name, self.biophysics.to_xml()),
                 name=self.name,
                 *[c.to_xml() for c in chain(self.parameters.values(), self.mappings.values())])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_CELL_NINEML + cls.element_name
        parameters = {}
        mappings = {}
        for child in element.getchildren():
            if child.tag == BIO_CELL_NINEML + Parameter.element_name:
                parameter = Parameter.from_xml(child)
                parameters[parameter.name] = parameter
            elif child.tag == BIO_CELL_NINEML + Mapping.element_name:
                mapping = Mapping.from_xml(child)
                mappings[mapping.name] = mapping
            elif child.tag == (nineml.extensions.morphology.MORPH_NINEML + 
                               nineml.extensions.morphology.Morphology.element_name):
                morphology = nineml.extensions.morphology.Morphology.from_xml(child)
            elif child.tag == (nineml.extensions.biophysics.BIO_NINEML + 
                               nineml.extensions.biophysics.BiophysicsModel.element_name):
                biophysics = nineml.extensions.biophysics.BiophysicsModel.from_xml(child)                
            elif child.tag == etree.Comment:
                pass
            else:
                raise Exception("<{}> elements may not contain <{}> elements"
                                .format(cls.element_name, child.tag))
        return cls(element.attrib['name'], parameters, mappings, morphology, biophysics)


class Parameter(object):

    element_name = 'Parameter'

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_CELL_NINEML + cls.element_name
        param_type = element.attrib['type']
        if param_type == IonicDynamicsParameter.type_name:
            obj = IonicDynamicsParameter.from_xml(element)
        elif param_type == GeometryParameter.type_name:
            obj = GeometryParameter.from_xml(element)
        elif param_type == InitialStateParameter.type_name:
            obj = InitialStateParameter.from_xml(element)
        else:
            raise Exception("Did not find recognisable '{}', '{}' or '{}'"
                            .format(IonicDynamicsParameter.type_name,
                                    GeometryParameter.type_name,
                                    InitialStateParameter.type_name))
        return obj


class IonicDynamicsParameter(Parameter):

    type_name = 'dynamics'
    mapping_tag_name = 'Mapping'
    component_tag_name = 'Component'
    name_tag_name = 'Name'
    
    def __init__(self, name, mapping, component, param_name):
        self.name = name
        self.mapping = mapping
        self.component = component
        self.param_name = param_name

    def __repr__(self):
        return ("Dynamics parameter {}->{} over mapping '{}'"
                .format(self.component, self.param_name, self.mapping))

    def to_xml(self):
        return E(self.element_name, 
                 E(self.mapping_tag_name, self.mapping),
                 E(self.component_tag_name, self.component),
                 E(self.name_tag_name, self.param_name),
                 name=self.name,
                 type=self.type_name)

    @classmethod
    def from_xml(cls, element):
        assert element.attrib['type'] == 'dynamics'
        name = element.attrib['name']
        mapping = element.find(BIO_CELL_NINEML + cls.mapping_tag_name).text.strip()
        component = element.find(BIO_CELL_NINEML + cls.component_tag_name).text.strip()
        param_name = element.find(BIO_CELL_NINEML + cls.name_tag_name).text.strip()
        return cls(name, mapping, component, param_name)


class InBuiltParameterType(Parameter):
    
    param_name_name = 'Name'
    division_name = 'Division'
    classification_attr_name = 'classification'
    
    def __init__(self, name, param_name, classification, segment_divisions):
        self.name = name
        self.param_name = param_name
        self.segment_divisions = segment_divisions
        self.classification = classification
    
    def __repr__(self):
        return ("{} parameter '{}' over {} segment divisions"
                .format(self.type_name, self.param_name, len(self.segment_divisions)))
    
    def to_xml(self):
        return E(self.element_name, 
                 E(self.param_name_name, self.param_name),
                 name=self.name,
                 type=self.type_name,
                 *[E(self.division_name, d) for d in self.segment_divisions],
                 **{self.classification_attr_name:self.classification})

    @classmethod
    def from_xml(cls, element):
        assert element.attrib['type'] == cls.type_name
        name = element.attrib['name']
        classification = element.attrib[cls.classification_attr_name]
        param_name = element.find(BIO_CELL_NINEML + cls.param_name_name).text.strip()
        segment_divisions = [d.text.strip() 
                             for d in element.findall(BIO_CELL_NINEML + cls.division_name)]
        return cls(name, param_name, classification, segment_divisions)


class GeometryParameter(InBuiltParameterType):

    type_name = 'geometry'


class InitialStateParameter(InBuiltParameterType):
    
    type_name = 'initialState'


class Mapping(object):

    element_name = 'Mapping'
    component_tag_name = 'Component'
    division_tag_name = 'Division'
    classification_attr_name = 'classification'

    def __init__(self, name, components, classification, segment_divisions):
        self.name = name
        self.components = components
        self.segment_divisions = segment_divisions
        self.classification = classification

    def __repr__(self):
        return ("'{}' mapping with biophysics(s): '{}'"
                .format(self.name, "', '".join([d.name for d in self.biophysicss])))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *chain([E(self.component_tag_name, c) for c in self.components],
                        [E(self.division_tag_name, d) for d in self.segment_divisions]),
                 **{self.classification_attr_name:self.classification})

    @classmethod
    def from_xml(cls, element):
        assert element.tag == BIO_CELL_NINEML + cls.element_name
        classification = element.attrib[cls.classification_attr_name]
        components = []
        divisions = []
        for child in element.getchildren():
            if child.tag == BIO_CELL_NINEML+cls.component_tag_name:
                components.append(child.text.strip())
            elif child.tag == BIO_CELL_NINEML+cls.division_tag_name:
                divisions.append(child.text.strip())
            else:
                raise Exception("Unrecognised child element '<{}>' found in <{}> element"
                                .format(child.tag, element.tag))
        return cls(element.attrib['name'], components, classification, divisions)
