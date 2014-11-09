import os.path
from urllib import urlopen
from lxml import etree
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace
E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})

uncert_dir = '/home/tclose/git/nineml/catalog/randomdistributions/uncertml_examples'
import_dir = '/home/tclose/git/nineml/catalog/randomdistributions/import'
for fname in os.listdir(uncert_dir):
    with open(os.path.join(uncert_dir, fname)) as f:
        in_xml = etree.parse(f)

    doc = E.NineML(out_xml, xmlns=nineml_namespace)
    etree.ElementTree(doc).write(os.path.join(import_dir, f), encoding="UTF-8",
                                 pretty_print=True, xml_declaration=True)
