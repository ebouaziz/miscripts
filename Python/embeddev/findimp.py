#!/usr/bin/env python

# Locate missing Python modules?

import os
import re

importcre = re.compile(r'^\s*((?:from\s+[\w+_\.]+\s+)?import\s+[\w+_]+)')

impset = set()
for (dirpath, dirnames, filenames) in os.walk('.'):
    dirnames[:] = [d for d in dirnames if not d.startswith('.')]
    for filename in filenames:
        if not filename.endswith('.py'):
            continue
        # print os.path.join(dirpath,filename)
        with open(os.path.join(dirpath,filename), 'rt') as pyfile:
            for line in pyfile.xreadlines():
                mo = importcre.match(line)
                if not mo:
                    continue
                impline = mo.group(1).strip(' \t')
                if impline not in impset:
                    impset.add(impline)
print """
#!/usr/bin/env python

print "Missing modules:"
for imp in [""", 
print ', \\\n    '.join(["'%s'" % i for i in sorted(impset)]), ']:'
print """    try:
        exec(imp)
    except ImportError:
        print "   ", imp
"""
