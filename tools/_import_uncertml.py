import os.path
from urllib import urlopen
from lxml import etree
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace
E = ElementMaker()

uncertml_ns = '{http://www.uncertml.org/2.0}'
len_ns = len(uncertml_ns)

uncert_dir = '/home/tclose/git/nineml/catalog/randomdistributions/uncertml_examples'
import_dir = '/home/tclose/git/nineml/catalog/randomdistributions/imported'
for fname in os.listdir(uncert_dir):
    with open(os.path.join(uncert_dir, fname)) as f:
        in_xml = etree.parse(f)
    distr_elem = in_xml.getroot()
    comp_name = distr_elem.tag[len_ns:]
    parameters = []
    for child in distr_elem.getchildren():
        parameters.append(child.tag[len_ns:])
    out_xml = E.ComponentClass(*([E.Parameter(name=p) for p in parameters] +
                                 [E.RandomDistribution(E.BuiltIn(
                                        uncertml=("http://www.uncertml.org/"
                                                  "distributions/{}"
                                                  .format(fname))))]),
                               name=comp_name)
    doc = E.NineML(out_xml, xmlns=nineml_namespace)
    etree.ElementTree(doc).write(os.path.join(import_dir, fname),
                                 encoding="UTF-8", pretty_print=True,
                                 xml_declaration=True)
