# Loosely based on an idea from
#   http://blog.efnx.com/formatting-gcc-g-output-using-php-in-textmate/

# Build from TextMate helper

import os
import re
import sys
import traceback

from subprocess import Popen, PIPE, STDOUT


def find_project_root(project_dir):
    if not os.path.isdir(project_dir):
        raise AssertionError("Invalid input directory '%s'" % project_dir)
    if not project_dir:
        raise AssertionError("Unable to find project path")
    tpath = os.path.join(project_dir, 'host', 'bin')
    if os.path.isdir(tpath):
        return project_dir
    else:
        return find_project_root(os.path.split(project_dir)[0])

sdk = True

try:
    curfile = sys.argv[1]
    curpath = os.path.dirname(curfile)
    if sdk:
        devpath = find_project_root(curpath)
        devdepth = len(devpath.split(os.sep))
        curdirs = curpath.split(os.sep)
        topdir = curdirs[devdepth]
        if devdepth+2 < len(curdirs):
            compdir = os.path.join(curdirs[devdepth+2])
            # special hack for npflasher and bootloader
            if compdir == 'src':
                compdir = None
        else:
            compdir = None
    else:
        devpath = curpath

    gcccre = re.compile(r'^(?P<file>[^:]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s'
                        r'(?P<type>warning|error):\s(?P<msg>.*)$')

    try:
        if topdir == 'ecos':
            builddir = os.path.join(devpath, 'build', topdir)
            args = []
        elif sdk:
            builddir = os.path.join(devpath, 'build', topdir)
            args = ['make', '-f', 'CMakeFiles/Makefile2']
            if len(sys.argv) > 3 and sys.argv[3].lower() == 'clean':
                args.append(os.sep.join(filter(None,
                            [curdirs[devdepth+1], compdir, 'clean'])))
            args.append(os.sep.join(filter(None,
                        [curdirs[devdepth+1], compdir, 'all'])))
            if compdir.endswith('_test'):
                args.append('%s_xz' % compdir)
        else:
            builddir, _ = os.path.split(curpath)
            args = ['make']
        build = Popen(args, bufsize=1, stdout=PIPE, stderr=STDOUT,
                      cwd=builddir)
        # (stdout, stderr) = build.communicate()
        print '''
<html>
  <head>
      <style type="text/css">
      body      {background:white; color:black; font-size: 85%;}
      .failure  {font-size: 100%; color: purple;}
      .success  {font-size: 100%; color: blue;}
      .gcc      {color: black;}
      .comment  {color: gray;}
      .warning  {color: #daa520;}
      .error    {color: #8b0000;}
      a         {text-decoration: none; color: gray;}
      a:hover   {background-color: #f0f0f8;}
      </style>
  </head>
  <body>
'''
        for line in build.stdout:
            mo = gcccre.match(line)
            if mo:
                # source = os.sep.join(mo.group('file').split(os.sep)[devdepth:])
                source = os.path.basename(mo.group('file'))
                line = mo.group('line')
                column = mo.group('col') or '1'
                type_ = mo.group('type')
                msg = mo.group('msg')
                href = 'txmt://open/?url=file://%s&line=%s&column=%s' % \
                    (mo.group('file'), line, column)
                msg = '<span class="%s">%s</span>' % (type_, msg)
                print "&nbsp;&nbsp;<a href=%s>%s:%s:%s %s</a><br/>" % \
                    (href, source, line, column, msg)
            else:
                if line.startswith(devpath):
                    print '<span class="gcc">%s</span><br/>' % \
                        line[len(devpath)+1:]
                else:
                    print '<span class="comment">%s<br/>' % line
        print '''
  </body>
</html>
'''
        build.wait()
    except OSError, e:
        raise AssertionError("Unable to build: %s with %s" %
                             (e, ' '.join(args)))

    if build.returncode != 0:
        print '<span class="failure">Failed</span>'
    else:
        print '<span class="success">Successful</span>'
    sys.exit(0)

except AssertionError, e:
    (type_, value, tb) = sys.exc_info()
    print "<h2>Error</h2>"
    print "<p><strong>%s</strong></p>" % value
    print "<table>"
    for filename, linenumber, funcname, text in traceback.extract_tb(tb):
        print '<tr><td><em>%s: %s</em></td></tr>' % \
            (filename, linenumber)
        print '<tr><td>&nbsp;&nbsp;&nbsp;%s</td></tr>' % text
    print "</table>"
    sys.exit(1)
