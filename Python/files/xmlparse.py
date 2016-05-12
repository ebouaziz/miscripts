import xml.etree.ElementTree as ET
import pprint

# Extract data from XML file

parser = ET.XMLTreeBuilder()

with open('maps.kml', 'rt') as f:
    et = ET.parse(f)

points = []
for e in et.getiterator():
    if e.tag.lower().endswith('geometrycollection'):
        for egc in e.getiterator():
            if egc.tag.lower().endswith('coordinates'):
                pt = filter(None, egc.text.split())
                points.extend([tuple(p.split(',')) for p in pt])
print points
