#!/usr/bin/env python

# State machine parser (whose syntax has been lost :-))

import os
import pprint
import re
import string
import sys

class Parser(object):
    """State machine parser"""

    REGEXES = \
    {
        'state' : r'(?P<level>=+)\s*(?P<name>[a-z][\w_]+)\s*(?P=level)',
        'init'  : r'@\s+\-\>(?P<iname>[a-z][\w_]+)',
        'entex' : r'(?P<type>entry|exit)\s+/(?P<eaction>[a-z][\w_]+)',
        'trans' : r'(?P<event>[a-z][\w_]+)\s+(?:\[(?P<guard>[a-z][\w_]+)\]\s*)?'
                  r'(?:/(?P<action>[a-z][\w_]+)\s*)?(?:\-\>\s*(?P<next>[a-z][\w_]+))?'
    }

    def __init__(self):
        regexes = [r'(?P<' + r + r'>' + self.REGEXES[r] + r')' for r in self.REGEXES]
        self.cre = re.compile(r'^(' + r'|'.join(regexes) + r')$', re.IGNORECASE)
        self.state = { '_parent' : None, '_level' : 0 }
        self.states = { 'Top': self.state }

    def _cb(self, mo):
        for type_, match in mo.groupdict().items():
            if match and type_ in self.REGEXES:
                return getattr(self, '_%s_cb' % type_)(match, mo)

    def _state_cb(self, match, mo):
        level = len(mo.group('level'))
        name = mo.group('name')
        if self.state['_level'] == level:
            pstate = self.state['_parent']
        elif level == self.state['_level']+1:
            pstate = self.state
        elif level > self.state['_level']:
            raise AssertionError('Cannot declare a substate with distance > 1')
        else:
            while level-1 < self.state['_level']:
                self.state = self.state['_parent']
                pstate = self.state['_parent']
                level += 1
        self.state = { '_parent' : pstate, '_level' : len(mo.group('level')) }
        if name in pstate:
            raise AssertionError("State '%s' redefined" % name)
        pstate[name] = self.state

    def _init_cb(self, match, mo):
        if 'init' in self.state:
            raise AssertionError("Init state refined for state '%s'" % \
                                    self.state_name(self.state))
        self.state['init'] = mo.group('iname')

    def _entex_cb(self, match, mo):
        if mo.group('type') in self.state:
            raise AssertionError("'%s' redefined for state '%s'" %
                (mo.group('type').title(), self.state_name(self.state)))
        self.state[mo.group('type')] = { 'action' : mo.group('eaction') }

    def _trans_cb(self, match, mo):
        events = self.state.setdefault(mo.group('event'), {})
        items = events[mo.group('guard') or ''] = {}
        for item in ('action', 'next'):
            if mo.group(item):
                items[item] = mo.group(item)

    def state_name(self, state):
        parent = state['_parent']
        for s in parent:
            if parent[s] == state:
                return s
        return 'Unknown'

    def parse(self, smf):
        try:
            for n,l in enumerate(smf):
                l = l.strip('\r').strip('\n')
                l = l[:l.find('#')].strip(' ')
                if self.cre.sub(self._cb, l):
                    raise AssertionError('Invalid syntax: %s' % l)
        except AssertionError, e:
            print >> sys.stderr, "%s at line %d" % (str(e), n)
            sys.exit(1)

    def flatten(self):
        def _flatten(children):
            results = {}
            for c in children:
                if c[0] in string.ascii_uppercase:
                    results.update( { c: children[c] } )
                    results.update(_flatten(children[c]))
            return results
        return _flatten(self.states)

    def link(self, flatstates):
        for statename in flatstates:
            state = flatstates[statename]
            if 'init' in state:
                if state['init'] not in flatstates:
                    raise AssertionError("Unknown initialization state '%s' for '%s" % \
                                         (state['init'], statename))
                state['init'] = flatstates[state['init']]
            for trans in [e for e in state if e[0] in string.ascii_lowercase and e != 'init']:
                for transition in state[trans].values():
                    if 'next' in transition:
                        if transition['next'] not in flatstates:
                            raise AssertionError("Unknown transition state '%s' for '%s'" % \
                                                 (transition['next'], statename))
                        transition['next'] = flatstates[transition['next']]

    def show(self):
        def _show(gparent, children):
            for c in children:
                if c[0] in string.ascii_uppercase:
                    print '%s [%s]' % (gparent, c)
                    gchildren = gparent + 1
                    _show(gchildren, children[c])
        _show(0, self.states)



with open('/Users/eblot/Downloads/TrayUnloadingDevice.sms', 'rt') as smf:
    parser = Parser()
    parser.parse(smf)
    parser.show()
    flatstates = parser.flatten()
    parser.link(flatstates)