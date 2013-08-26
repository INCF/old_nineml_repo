import urllib
from itertools import chain
from lxml import etree
from lxml.builder import E

morphology_namespace = 'http://www.nineml.org/Morphology'
MORPH_NINEML = "{%s}" % morphology_namespace

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
    return Morphology.from_xml(root)


class Morphology(object):

    element_name = 'morphology'

    def __init__(self, name, segments, classifications):
        self.name = name
        self.segments = segments
        self.classifications = classifications

    def to_xml(self):
        return E(self.element_name,
                 name=self.name
                 * [c.to_xml() for c in chain(self.segments, self.classfications)])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        segments = []
        classifications = []
        for child in element.getchildren():
            if child.tag == MORPH_NINEML + Segment.element_name:
                segments.append(Segment.from_xml(child))
            elif child.tag == MORPH_NINEML + Classification.element_name:
                classifications.append(Classification.from_xml(child))
            elif child.tag == etree.Comment:
                pass
            else:
                raise Exception("<{}> elements may not contain <{}> elements"
                                .format(cls.element_name, child.tag))
        return cls(element.attrib['name'], segments, classifications)


class Segment(object):

    element_name = 'segment'

    def __init__(self, name, distal, proximal=None, parent=None):
        assert int(proximal is None) + int(parent is None) == 1 # Only one of proximal and parent can be used 
        self.name = name
        self.proximal = proximal
        self.parent = parent
        self.distal = distal

    def to_xml(self):
        return E(self.element_name,
                 self.proximal.to_xml(),
                 self.distal.to_xml())

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        distal = DistalPoint.from_xml(element.find(MORPH_NINEML + DistalPoint.element_name))
        prox_element = element.find(MORPH_NINEML + ProximalPoint.element_name)
        parent_element = element.find(MORPH_NINEML + ParentSegment.element_name)
        if prox_element is not None:
            if parent_element is not None:
                raise Exception("<{}> and <{}> tags cannot be used together in segment '{}'"
                                .format(ProximalPoint.element_name, ParentSegment.element_name, 
                                        element.attrib['name']))
            proximal = ProximalPoint.from_xml(prox_element)
            parent = None
        elif parent_element is not None:
            parent = ParentSegment.from_xml(parent_element)
            proximal = None
        else:
            raise Exception("Either <{}> or <{}> must be provided to segment '{}'"
                            .format(ProximalPoint.element_name, ParentSegment.element_name, 
                                        element.attrib['name']))
        return cls(element.attrib['name'], distal, proximal=proximal, parent=parent)


class Point3D(object):

    def __init__(self, x, y, z, diameter):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.diameter = float(diameter)

    def __repr__(self):
        return "[{}, {}, {}], diam:{}".format(self.x,self.y,self.z,self.diameter)

    def to_xml(self):
        return E(self.element_name,
                 x=self.x, y=self.y, z=self.z, diameter=self.diameter)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        return cls(element.attrib['x'], element.attrib['y'], element.attrib['z'], 
                   element.attrib['diameter'])


class ProximalPoint(Point3D):

    element_name = 'proximal'


class DistalPoint(Point3D):

    element_name = 'distal'


class ParentSegment(object):
    
    element_name = 'parent'
    
    def __init__(self, segment_name, fraction_along):
        self.segment_name = segment_name
        self.fraction_along = fraction_along
        
    def to_xml(self):
        opt_kwargs = {}
        if self.fraction_along is not None:
            opt_kwargs['fractionAlong'] = self.fraction_along
        return E(self.element_name, segment=self.segment_name, **opt_kwargs)
    
    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        return cls(element.attrib['segment'], element.attrib.get('fractionAlong', None))


class Classification(object):

    element_name = 'classification'
    
    def __init__(self, name, divisions):
        self.name = name
        self.divisions = divisions
        
    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[d.to_xml() for d in self.divisions])
        
    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        divisions = []
        for child in element.getchildren():
            divisions.append(Division.from_xml(child))
        return cls(element.attrib['name'], divisions)    

class Division(object):

    element_name = 'division'

    def __init__(self, name, members):
        self.name = name
        self.members = members
        
    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[d.to_xml() for d in self.members])
        
    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        members = []
        for child in element.getchildren():
            members.append(Member.from_xml(child))
        return cls(element.attrib['name'], members)
    
    
class Member(object):
    
    element_name = 'member'
    
    def __init__(self, segment_name):
        self.segment_name = segment_name
        
    def __repr__(self):
        return "segment: {}".format(self.segment_name)
        
    def to_xml(self):
        return E(self.element_name, self.segment_name)
    
    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        return cls(element.text)
        
        
if __name__ == '__main__':
    morph = parse('/home/tclose/Desktop/test_morphology.9ml')
    print morph
    
    
