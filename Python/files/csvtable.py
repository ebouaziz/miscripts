#!/usr/bin/env python2.7

# Show CSV as table

import petl as etl
import csv

rasu = etl.fromcsv(source='file.csv',
                   encoding='iso8859-1', 
                   delimiter=';')
print etl.util.vis.look(rasu)

