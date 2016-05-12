#!/usr/bin/env python

# Inject TV show into iTunes

# system
import datetime
import os
import re
import time
import sys
import urllib
from optparse import OptionParser
from ConfigParser import SafeConfigParser
# Mac OS X
import appscript
import mactypes

# To get episode summary, some extra Python packages are required
#port install py25-lxml
#port install py25-libxslt
#port install py25-libxml2
#easy_install-2.5 pyxml

try:
    import libxml2dom
    #from xml.dom.ext.reader import HtmlLib
except ImportError:
    # missing XML parser lib, do not try to retrieve summary
    print >> sys.stderr, \
        "Warning: libxml2dom missing, no summary can be retrieved"


class EasyConfigParser(SafeConfigParser):
    """ConfigParser extension to support default config values
    """
    def get(self, section, option, default=None):
        if not self.has_section(section):
            return default
        if not self.has_option(section, option):
            return default
        return SafeConfigParser.get(self, section, option)


class Injector(object):
    """
    """
    def __init__(self, configfile, topdir, refdir):
        # generate regular expression to parse video files
        today = datetime.date.today()
        monthre = '|'.join([today.replace(month=m).strftime("%b") \
                            for m in range(1,13)])
        self.filecre = re.compile(r'^(?P<show>.*)\.[sS](?P<season>\d\d)[eE]' \
                                  r'(?P<episode>\d\d)')
        self.showbcre = re.compile(r'(?P<season>\d+)\-\s?(?P<episode>\d+).*' \
                                  r'\s(?P<date>\d+\s(' + monthre + \
                                  r')\s\d+).*' \
                                  r'<a.*\shref="(?P<url>.*)"' + \
                                  r'>(?P<title>.*)</a>')
        # application handlers
        self.qtime = appscript.app('QuickTime Player')
        self.itunes = appscript.app('iTunes')
        self._load_config(configfile, topdir, refdir)
        self._query_shows()

    def _load_config(self, configfile, topdir):
        """Load configuration from the configuration file"""
        parser = EasyConfigParser()
        if not parser.read(configfile):
            raise AssertionError('Unable to read config file %s' % configfile)
        self.epguides = parser.get('config', 'epguides', 'http://epguides.com')
        self.topdir = parser.get('config', 'topdir', topdir)
        if not self.topdir:
            raise AssertionError('Top directory not defined in %s' % \
                                    configfile)
        self.refdir = parser.get('config', 'refdir', refdir)
        if not self.refdir:
            raise AssertionError('Reference directory not defined in %s' % \
                                    configfile)
        os.makedirs(self.refdir)
        extensions = parser.get('config', 'extensions', 'avi')
        self.exts = [e.strip() for e in extensions.split(',')]
        self.playlistname = parser.get('config', 'playlist', 'ImportAVI')
        self.map = dict()
        for option in parser.options('map'):
            self.map[option.lower()] = parser.get('map', option).strip()
        self.ignore = []
        for option in parser.options('ignore'):
            if parser.get('ignore', option).strip():
                self.ignore.append(option.lower())

    def _query_shows(self):
        """Load existing TV shows from iTunes"""
        self.tvshows = [t for t in self.itunes.tracks() \
                            if t.video_kind() == appscript.k.TV_show]

    def _show_exists(self, show, season, episode):
        """Test whether the show already exists in iTunes"""
        for track in self.tvshows:
            if (show == track.show()) and \
               (episode == int(track.episode_number() or 0)) and \
               (season == int(track.season_number() or 0)):
                print "Show %s Track %s.%s already in iTunes, skipping" % \
                    (show, season, episode)
                return True
        return False

    def _make_quicktime_reffile(self, filename):
        """Creates a reference file so that iTunes can manage a foreign file"""
        filesize = os.stat(filename)[6]
        reffilename = os.path.join(self.refdir,
                                   '%s.mov' % os.path.basename(filename))
        try:
            self.qtime.open(filename)
        except appscript.reference.CommandError, e:
            print >> sys.stderr, "Cannot open %s in QuickTime" % filename
            return None
        lastsize = 0
        # increase nochange if quicktime is slow to import files
        nochange = 2
        while nochange:
            size = self.qtime.documents[1]().data_size()
            if size == lastsize and size:
                nochange = max(nochange-1,0)
            else:
                nochange = 2
            lastsize = size
            time.sleep(1)
            print "\rFile %s %02u%% %u" % \
                (filename, (100*size)/filesize, nochange),
            sys.stdout.flush()
        self.qtime.save(self.qtime.documents[1],in_=reffilename)
        self.qtime.close(self.qtime.documents[1])
        print " saved"
        return reffilename

    def _inject(self, filename):
        """Inject the reference file into iTunes and define track properties"""
        # Search for an exising playlist
        pl = None
        for p in self.itunes.playlists():
            if p.name() == self.playlistname:
                pl = p
                break
        if not pl:
            pl = self.itunes.make(new = appscript.k.playlist,
                                  with_properties = \
                                    {appscript.k.name: self.playlistname})
        macref = mactypes.File(filename)
        track = self.itunes.add(macref,to = pl)
        return track

    def _retrieve_info(self, show, season, episode):
        """Retrieve the episode information"""
        epurl = '%s/%s' % (self.epguides, show)
        try:
            epguide = urllib.urlopen(epurl)
        except IOError:
            print >> sys.stderr, "Cannot connect to %s" % self.epguides
            return None
        epdate = None
        url = None
        title = None
        year = None
        print "URL: %s" % epurl
        for line in epguide.readlines():
            mo = self.showbcre.search(line)
            if mo:
                if not (season == int(mo.group('season')) and
                        episode == int(mo.group('episode'))):
                        continue
                epdate = datetime.datetime.strptime(mo.group('date'),
                                                    r'%d %b %y').date()
                title = mo.group('title')
                url = mo.group('url')
                year = int(epdate.year)
                print "Episode: %s %d.%d %s: %s" % \
                    (show, season, episode, epdate, title)
        epguide.close()
        if not title or not year:
            return None
        return (title, year, url)

    def _retrieve_summary(self, url):
        """Retrieve the episode summary"""
        # reader = HtmlLib.Reader()
        if not url:
            print >> sys.stderr, 'Warning: no URL for summary'
            return ''
        print "Retrieving %s" % url
        show = urllib.urlopen(url)
        showstr = show.read()
        # Website sometimes contains invalid characters, which cause the
        # DOM parser to fail. Discard any non-ASCII character
        showstr = showstr.decode('ascii', 'ignore')
        show.close()
        doc = libxml2dom.parseString(showstr, html=1)
        for node in doc.getElementsByTagName('p'):
            if node.hasAttribute('class'):
                if 'deck' in node.getAttribute('class'):
                    for child_node in node.childNodes:
                        if child_node.nodeType == child_node.TEXT_NODE:
                            summary = child_node.nodeValue.strip()
                            if summary:
                                return summary
        return ''

    def run(self):
        """Process video files, one after another"""
        for root, dirs, files in os.walk(self.topdir):
            for f in files:
                (base, ext) = os.path.splitext(f)
                if ext[1:].lower() in self.exts:
                    filename = os.path.join(root, f)
                    filemo = self.filecre.match(os.path.basename(filename))
                    if not filemo:
                        print >> sys.stderr, "Filename %s does not match " \
                                "any supported pattern" % filename
                        continue
                    show = filemo.group('show')
                    season = int(filemo.group('season'))
                    episode = int(filemo.group('episode'))
                    for ignore in self.ignore:
                        if -1 != show.lower().find(ignore):
                            print 'Show %s discarded, skipping' % show
                            show = None
                            break
                    if not show:
                        continue
                    showname = show
                    if show.lower() in self.map:
                        showname = self.map[show.lower()]
                    if self._show_exists(show, season, episode):
                        continue
                    info = self._retrieve_info(showname, season, episode)
                    if not info:
                        print "Unable to retrieve info for %s" % filename
                        continue
                    (title, year, url) = info
                    ref = self._make_quicktime_reffile(filename)
                    if not ref:
                        continue
                    summary = ''
                    if 'libxml2dom' in sys.modules:
                        summary = self._retrieve_summary(url)
                    track = self._inject(ref)
                    track.video_kind.set(appscript.k.TV_show)
                    track.show.set(show)
                    track.season_number.set(season)
                    track.episode_number.set(episode)
                    track.episode_ID.set(title)
                    track.year.set(year)
                    track.description.set(summary)


if __name__ == '__main__':
    usage = 'Usage: %prog [options]\n'\
            '  Inject TV show into iTunes'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-c', '--config', dest='config',
                         help='configuration file')
    optparser.add_option('-d', '--dir', dest='topdir',
                         help='search path for video files')
    optparser.add_option('-r', '--refdir', dest='refdir',
                         help='path to store reference files')
    (options, args) = optparser.parse_args(sys.argv[1:])
    if not options.config:
        raise AssertionError('No configuration file')
    injector = Injector(options.config, options.topdir, options.refdir)
    injector.run()
