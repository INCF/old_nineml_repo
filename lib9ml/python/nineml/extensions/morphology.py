import urllib
from itertools import chain
from lxml import etree
from lxml.builder import E
import numpy

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
        # Set root segment and children references
        self.root = None
        for seg in segments.itervalues():
            if seg.parent_ref:
                parent = segments[seg.parent_ref.name]
                parent.children.append(seg)
                seg.parent_ref.segment = parent
            else:
                if self.root:
                    raise Exception("Multiple root segments found ({} and {})"
                                    .format(self.root.name,
                                            seg.parent_ref.name))
                else:
                    self.root = seg
        if self.root is None:
            raise Exception("No root segment found in tree -> circular "
                            "references exist")
        self.classifications = classifications
        for classification in self.classifications.itervalues():
            for seg_class in classification.classes.itervalues():
                seg_class._set_members(self)

    @property
    def segments(self):
        """
        Segments are not stored directly as a flat list to allow branches
        to be edited by altering the children of segments. This iterator is
        then used to flatten the list of segments
        """
        return chain([self.root], self.root.all_children)

    def segment(self, name):
        match = [seg for seg in self.segments if seg.name == name]
        #TODO: Need to check this on initialisation
        assert len(match) <= 1, "Multiple segments with key '{}'".format(name)
        if not len(match):
            raise KeyError("Segment '{}' was not found".format(name))
        return match[0]

    def __repr__(self):
        return ("Morphology '{}' with {} segment(s) and {} classification(s)"
                .format(self.name, len(self.segments),
                        len(self.classifications)))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[c.to_xml() for c in chain(self.segments,
                                             self.classifications.values())])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        segments = {}
        classifications = {}
        for child in element.getchildren():
            if child.tag == MORPH_NINEML + Segment.element_name:
                segment = Segment.from_xml(child)
                segments[segment.name] = segment
            elif child.tag == MORPH_NINEML + Classification.element_name:
                classification = Classification.from_xml(child)
                classifications[classification.name] = classification
            elif child.tag == etree.Comment:
                pass
            else:
                raise Exception("<{}> elements may not contain <{}> elements"
                                .format(cls.element_name, child.tag))
        return cls(element.attrib['name'], segments, classifications)


class Segment(object):

    element_name = 'segment'

    def __init__(self, name, distal, proximal=None, parent_ref=None):
        if proximal is None and parent_ref is None:
            raise Exception("Only one of proximal and parent_ref can be used")
        elif proximal is not None and parent_ref is not None:
            raise Exception("Proximal or parent_ref must be supplied")
        self.name = name
        self._proximal = proximal
        self.parent_ref = parent_ref
        self.distal = distal
        self.children = []
        self.classes = []

    @property
    def proximal(self):
        if self.parent_ref:
            if self.parent_ref.fraction_along:
                pos = (self.parent.proximal.pos +
                       (self.parent.distal.pos /
                        self.parent_ref.fraction_along))
            else:
                pos = self.parent_ref.segment.distal.pos
            return Point3D(pos[0], pos[1], pos[2], self.distal.diameter)
        else:
            return self._proximal

    @property
    def length(self):
        return numpy.sqrt(numpy.sum(self.distal.pos - self.proximal.pos))

    def diameter(self, fraction_along=1.0):
        return (self.proximal.diameter * (1.0 - fraction_along) +
                self.distal.diameter * fraction_along)

    @property
    def parent(self):
        try:
            return self.parent_ref.segment
        except AttributeError:
            return None

    @property
    def all_children(self):
        for child in self.children:
            yield child
            for childs_child in child.all_children:
                yield childs_child

    def __repr__(self):
        if self.parent_ref:
            p = "parent_ref: ({})".format(repr(self.parent_ref))
        else:
            p = "proximal: ({})".format(repr(self._proximal))
        return "Segment: '{}', {}, distal: ({})".format(self.name, p,
                                                        self.distal)

    def to_xml(self):
        return E(self.element_name,
                 (self.parent_ref.to_xml()
                  if self.parent_ref else self._proximal.to_xml()),
                 self.distal.to_xml(),
                 name=self.name)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        distal = DistalPoint.from_xml(element.find(MORPH_NINEML +
                                                   DistalPoint.element_name))
        prox_element = element.find(MORPH_NINEML + ProximalPoint.element_name)
        parent_element = element.find(MORPH_NINEML +
                                      ParentReference.element_name)
        if prox_element is not None:
            if parent_element is not None:
                raise Exception("<{}> and <{}> tags cannot be used together "
                                "in segment '{}'"
                                .format(ProximalPoint.element_name,
                                        ParentReference.element_name,
                                        element.attrib['name']))
            proximal = ProximalPoint.from_xml(prox_element)
            parent_ref = None
        elif parent_element is not None:
            parent_ref = ParentReference.from_xml(parent_element)
            proximal = None
        else:
            raise Exception("Either <{}> or <{}> must be provided to segment "
                            "'{}'".format(ProximalPoint.element_name,
                                          ParentReference.element_name,
                                          element.attrib['name']))
        return cls(element.attrib['name'], distal, proximal=proximal,
                   parent_ref=parent_ref)


class Point3D(object):

    def __init__(self, x, y, z, diameter):
        self.pos = numpy.array([float(x), float(y), float(z)])
        self.diameter = float(diameter)

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    @property
    def z(self):
        return self.pos[2]

    def __repr__(self):
        return "[{}, {}, {}, diam:{}]".format(self.x, self.y, self.z,
                                              self.diameter)

    def to_xml(self):
        return E(self.element_name,
                 x=str(self.x), y=str(self.y), z=str(self.z),
                 diameter=str(self.diameter))

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        return cls(element.attrib['x'], element.attrib['y'],
                   element.attrib['z'], element.attrib['diameter'])


class ProximalPoint(Point3D):

    element_name = 'proximal'


class DistalPoint(Point3D):

    element_name = 'distal'


class ParentReference(object):

    element_name = 'parent'

    def __init__(self, segment_name, fraction_along):
        self.name = segment_name
        self.fraction_along = float(fraction_along)
        self.segment = None

    def __repr__(self):
        rep = "segment: {}".format(self.name)
        if self.fraction_along is not None:
            rep += ", fraction along: {}".format(self.fraction_along)
        return rep

    def to_xml(self):
        opt_kwargs = {}
        if self.fraction_along != 1.0:
            opt_kwargs['fractionAlong'] = str(self.fraction_along)
        return E(self.element_name, segment=self.name, **opt_kwargs)

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        return cls(element.attrib['segment'],
                   float(element.attrib.get('fractionAlong', 1.0)))


class Classification(object):

    element_name = 'classification'

    def __init__(self, name, classes):
        self.name = name
        self.classes = classes

    def __getitem__(self, key):
        return self.classes[key]

    def __repr__(self):
        return ("'{}' classification with division(s): '{}'"
                .format(self.name,
                        "', '".join([k for k in self.classes.keys()])))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[c.to_xml() for c in self.classes.itervalues()
                   if not c.empty()])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        classes = {}
        for child in element.getchildren():
            seg_class = SegmentClass.from_xml(child)
            classes[seg_class.name] = seg_class
        return cls(element.attrib['name'], classes)


class SegmentClass(object):

    element_name = 'class'
    member_name = 'member'

    def __init__(self, name, members):
        self.name = name
        # Temporarily store the member names before the classes are stored
        # in the segments themselves
        self._member_names = members
        self._morphology = None

    def _set_members(self, morphology):
        self._morphology = morphology
        for seg in morphology.segments:
            if seg.name in self._member_names:
                seg.classes.append(self.name)
        # Clear the member names as class members will now be accessed by
        # the class list in the segments themselves
        self._member_names = []

    def __iter__(self):
        return (seg for seg in self._morphology.segments
                if self.name in seg.classes)

    def __len__(self):
        return len(list(iter(self)))

    def __repr__(self):
        return ("'{}' segment class with {} member(s)"
                .format(self.name, 0))

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[E(self.member_name, m.name) for m in self.members])

    @classmethod
    def from_xml(cls, element):
        assert element.tag == MORPH_NINEML + cls.element_name
        members = []
        for child in element.getchildren():
            assert child.tag == MORPH_NINEML + cls.member_name
            members.append(child.text)
        return cls(element.attrib['name'], members)
