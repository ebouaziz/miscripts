#!/usr/bin/env python3


"""Documentation
"""

from argparse import ArgumentParser, FileType
from cmd import Cmd
from re import compile as recompile
from shutil import get_terminal_size
from sys import exit, modules, stderr
from textwrap import shorten
from traceback import format_exc
try:
    import readline as rl
except ImportError:
    rl = None


class Warning(object):
    """
    """

    DEFAULT_LANGUAGE = 'C'

    LANGUAGES = {
        'C': 'c',
        'X': 'c++',
        'O': 'objc',
        'P': 'openmp',
        'L': 'opencl',
    }

    def __init__(self, name, options, *controllers):
        name = name.lstrip('-').lstrip('W')
        if not name:
            raise ValueError('Warning with no name')
        self.name = name
        self.default = 'D' in options
        self.useless = 'U' in options
        self.selected = None
        self.controlled = set()
        languages = [lang for lang in self.LANGUAGES if lang in options]
        if len(languages) > 1:
            raise ValueError('Too many languages: %s' % ','.join(languages))
        self.language = self.LANGUAGES[languages and languages[0] or
                                       self.DEFAULT_LANGUAGE]
        self.controllers = set(controllers)
        self.controllees = set()

    @property
    def is_active(self):
        if self.selected is not None:
            # explicilty enabled or disabled
            return self.selected
        if self.controlled:
            # enabled or disabled via a master warning
            return True
        # fallback to default enablement
        return self.default

    def is_lang(self, language):
        return self.language == language

    def add_control(self, controllees):
        if isinstance(controllees, str):
            self.controllees.add(controllees)
        else:
            self.controllees.update(controllees)

    def discard_control(self, controllees):
        if not controllees:
            return
        self.controllees -= controllees


class WarningError(ValueError):
    """Error to report invalid chooser requests
    """


class WarningChooser(object):
    """
    """

    DW_CRE = recompile(r'\(\-W([\w\-]+)\)')

    def __init__(self, language=None):
        self._all_warnings = {}
        self._language = Warning.LANGUAGES[language or
                                           Warning.DEFAULT_LANGUAGE]
        self._warnings = {}

    def load(self, fp):
        if rl:
            delims = rl.get_completer_delims()
            for nodelim in '-':
                delims = delims.replace(nodelim, '')
            rl.set_completer_delims(delims)
        for lpos, line in enumerate(fp, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                options, warnings = line.split('-', 1)
                if ' ' in warnings:
                    warning, subwarns = warnings.split(' ', 1)
                else:
                    warning, subwarns = warnings, ''
                w = Warning(warning, options, *self.DW_CRE.findall(subwarns))
                self._all_warnings[w.name] = w
            except Exception as ex:
                print('Error: %s @ line %d: %s' % (str(ex), lpos, line),
                      file=stderr)
                continue
        for warning in self._all_warnings.values():
            for ctrlname in warning.controllers:
                try:
                    controller = self._all_warnings[ctrlname]
                except KeyError:
                    raise WarningError('Invalid warning %s controlled by %s' %
                                       (ctrlname, warning.name))
                controller.add_control(warning.name)
        self.reset()

    def reset(self):
        self._warnings = {wn: wo for wn,wo in self._all_warnings.items()
                          if wo.is_lang(self._language) and not wo.useless}
        for warning in self._warnings.values():
            discarded = set()
            for ctrlname in warning.controllees:
                if ctrlname not in self._warnings:
                    discarded.add(ctrlname)
            warning.discard_control(discarded)

    def enumerate(self, kind=None):
        if kind is None or kind == 'all':
            return set(self._warnings.keys())
        if kind == 'active':
            return set([wn for wn, wo in self._warnings.items()
                    if wo.is_active])
        if kind == 'nonactive':
            return set([wn for wn, wo in self._warnings.items()
                    if not wo.is_active])
        if kind == 'selected':
            selection = set()
            for wn, wo in self._warnings.items():
                if wo.selected is None:
                    continue
                if wo.selected:
                    selection.add(wn)
                else:
                    selection.add('no-%s' % wn)
            return selection

    def show(self, kind=None, showsub=True):
        selection = self.enumerate(kind)
        for warn in sorted(selection):
            if warn.startswith('no-'):
                rootwarn = warn[3:]
            else:
                rootwarn = warn
            ctrlstr = ', '.join(sorted(self._warnings[rootwarn].controllees))
            main = '  %s' % warn
            if showsub and ctrlstr:
                cols = get_terminal_size((80, 25))[0]
                info = '  %s)' % shorten(' '.join((main, '(%s' % ctrlstr)),
                                       width=cols-4,
                                       break_on_hyphens=False,
                                       placeholder=' ...')
            else:
                info = main
            print(info)
        print('%d out of %d' % (len(selection), len(self._warnings)))

    def enable(self, name, enable):
        try:
            warning = self._warnings[name]
        except KeyError:
            raise WarningError('No such warning: %s' % name)
        if warning.selected == enable:
            raise WarningError('Warning %s already %sselected' %
                               (name, not enable and 'not ' or ''))
        if warning.is_active == enable:
            print('Warning %s was already automatically %sselected' %
                  (name, not enable and 'not ' or ''))
        warning.selected = enable
        for wn in sorted(self._get_controllees(name)):
            if enable:
                self._warnings[wn].controlled.add(name)
            else:
                self._warnings[wn].controlled.discard(name)

    def clear(self, name):
        try:
            warning = self._warnings[name]
        except KeyError:
            raise WarningError('No such warning: %s' % name)
        warning.selected = None

    def _get_controllees(self, name):
        controllees = set(self._warnings[name].controllees)
        for wn in self._warnings[name].controllees:
            controllees.update(self._get_controllees(wn))
        return controllees


class WarningShell(Cmd):
    """
    """

    intro = 'Welcome to the Warning selector\n'
    prompt = 'Ws> '

    def __init__(self, chooser):
        super(WarningShell, self).__init__()
        self._chooser = chooser

    def do_reset(self, arg):
        """Reset the warning list"""
        self._chooser.reset()

    def do_quit(self, arg):
        """Exit the application"""
        selection = self._chooser.enumerate('selected')
        for wn in sorted(selection):
            print('-W%s' % wn)
        return True

    def do_all(self, arg):
        """Show all available warnings"""
        self._chooser.show('all')

    def do_active(self, arg):
        """Show active warnings"""
        self._chooser.show('active')

    def do_nonactive(self, arg):
        """Show non-activated warnings"""
        self._chooser.show('nonactive')

    def do_selected(self, arg):
        """Show non-activated warnings"""
        self._chooser.show('selected')

    def complete_enable(self, text, line, begidx, endidx):
        candidates = self._chooser.enumerate('nonactive')
        return [w for w in candidates if w.startswith(text)]

    def do_enable(self, arg):
        """Select a new warning"""
        if not arg:
            return
        try:
            self._chooser.enable(arg, True)
        except WarningError as ex:
            print(str(ex))

    def complete_disable(self, text, line, begidx, endidx):
        candidates = self._chooser.enumerate('active')
        return [w for w in candidates if w.startswith(text)]

    def do_disable(self, arg):
        """Select a new warning"""
        if not arg:
            return
        try:
            self._chooser.enable(arg, False)
        except WarningError as ex:
            print(str(ex))

    def complete_clear(self, text, line, begidx, endidx):
        candidates = [w.startswith('no-') and w[3:] or w for w in
                      self._chooser.enumerate('selected')]
        return [w for w in candidates if w.startswith(text)]

    def do_clear(self, arg):
        """Reset activation status of a warnings"""
        if not arg:
            return
        try:
            self._chooser.clear(arg)
        except WarningError as ex:
            print(str(ex))


def main():
    """Main routine"""

    debug = True
    try:
        argparser = ArgumentParser(description=modules[__name__].__doc__)
        argparser.add_argument('-f', '--file', type=FileType('rt'),
                               required=True,
                               help='increase verbosity')
        argparser.add_argument('-l', '--language',
                               choices=Warning.LANGUAGES.values(),
                               help='increase verbosity')
        argparser.add_argument('-d', '--debug', action='store_true',
                               help='enable debug mode')
        args = argparser.parse_args()
        debug = args.debug

        wc = WarningChooser()
        wc.load(args.file)
        ws = WarningShell(wc)
        ws.cmdloop()

    except Exception as e:
        print('\nError: %s' % e, file=stderr)
        if debug:
            print(format_exc(chain=False), file=stderr)
        exit(1)
    except KeyboardInterrupt:
        exit(2)


if __name__ == '__main__':
    main()

