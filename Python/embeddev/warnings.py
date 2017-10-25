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
        self.controlled = None
        languages = [lang for lang in self.LANGUAGES if lang in options]
        if len(languages) > 1:
            raise ValueError('Too many languages: %s' % ','.join(languages))
        self.language = self.LANGUAGES[languages and languages[0] or
                                       self.DEFAULT_LANGUAGE]
        self.controllers = set(controllers)
        self.controllees = set()

    @property
    def enabled(self):
        return bool(self.selected or self.default)

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
        self._warnings = {}
        self._language = Warning.LANGUAGES[language or
                                           Warning.DEFAULT_LANGUAGE]
        self._selected = {}

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
                self._warnings[w.name] = w
            except Exception as ex:
                print('Error: %s @ line %d: %s' % (str(ex), lpos, line),
                      file=stderr)
                continue
        for warning in self._warnings.values():
            for ctrlname in warning.controllers:
                try:
                    controller = self._warnings[ctrlname]
                except KeyError:
                    raise WarningError('Invalid warning %s controlled by %s' %
                                       (ctrlname, warning.name))
                controller.add_control(warning.name)
        self.reset()

    def reset(self):
        self._selected = {wn: wo for wn,wo in self._warnings.items()
                          if wo.is_lang(self._language) and not wo.useless}
        for warning in self._selected.values():
            discarded = set()
            for ctrlname in warning.controllees:
                if ctrlname not in self._selected:
                    discarded.add(ctrlname)
            warning.discard_control(discarded)

    def enumerate(self, wfilter=None):
        warnings = self._selected
        if wfilter is None:
            filter_func = lambda w: True
        else:
            filter_func = lambda w: (w.enabled == wfilter) and \
                                        (w.controlled is None or \
                                             w.controlled == wfilter)
        selection = [wn for wn in warnings if filter_func(warnings[wn])]
        return selection

    def enumerate_all(self):
        return self.enumerate()

    def enumerate_selection(self, strict=False):
        selection = self.enumerate(True)
        if strict:
            selection = [wn for wn in selection if self._selected[wn].selected]
        return selection

    def enumerate_available(self):
        return self.enumerate(False)

    def show(self, selection, show_controllees=True):
        for warn in sorted(selection):
            ctrlstr = ', '.join(sorted(self._selected[warn].controllees))
            main = '  %s' % warn
            if show_controllees and ctrlstr:
                cols = get_terminal_size((80, 25))[0]
                info = '  %s)' % shorten(' '.join((main, '(%s' % ctrlstr)),
                                       width=cols-4,
                                       break_on_hyphens=False,
                                       placeholder=' ...')
            else:
                info = main
            print(info)
        print('%d out of %d' % (len(selection), len(self._selected)))

    def show_all(self):
        selection = self.enumerate()
        self.show(selection)

    def show_selection(self):
        selection = self.enumerate_selection()
        self.show(selection)

    def show_available(self):
        selection = self.enumerate_available()
        self.show(selection)

    def show_enabled(self):
        selection = self.enumerate_selection(True)
        self.show(selection, False)

    def enable(self, name, enable):
        try:
            warning = self._selected[name]
        except KeyError:
            raise WarningError('No such warning: %s' % name)
        if warning.selected == enable:
            raise WarningError('Warning %s already %sselected' %
                               (name, not enable and 'not ' or ''))
        if warning.default == enable or warning.controlled == enable:
            print('Warning %s was already automatically %sselected' %
                  (name, not enable and 'not ' or ''))
        warning.selected = enable
        for wn in sorted(self._get_controllees(name)):
            self._selected[wn].controlled = enable

    def _get_controllees(self, name):
        controllees = set(self._selected[name].controllees)
        for wn in self._selected[name].controllees:
            controllees.update(self._get_controllees(wn))
        return controllees


class WarningShell(Cmd):
    """
    """

    intro = 'Warning selector'
    prompt = 'Ws> '

    def __init__(self, chooser):
        super(WarningShell, self).__init__()
        self._chooser = chooser

    def do_active(self, arg):
        """Show active warnings"""
        self._chooser.show_selection()

    def do_list(self, arg):
        """Show all selected warnings"""
        self._chooser.show_enabled()

    def do_view(self, arg):
        """Show all warnings"""
        self._chooser.show_all()

    def do_available(self, arg):
        """Show non-activated warnings"""
        self._chooser.show_available()

    def do_reset(self, arg):
        """Reset the warning list"""
        self._chooser.reset()

    def do_quit(self, arg):
        """Exit the application"""
        selection = self._chooser.enumerate_selection(True)
        for wn in selection:
            print('-W%s' % wn)
        return True

    def complete_enable(self, text, line, begidx, endidx):
        return [w for w in self._chooser.enumerate_available()
                if w.startswith(text)]

    def do_enable(self, arg):
        """Select a new warning"""
        if not arg:
            return
        try:
            self._chooser.enable(arg, True)
        except WarningError as ex:
            print(str(ex))

    def complete_disable(self, text, line, begidx, endidx):
        return [w for w in self._chooser.enumerate_selection()
                if w.startswith(text)]

    def do_disable(self, arg):
        """Select a new warning"""
        if not arg:
            return
        try:
            self._chooser.enable(arg, False)
        except WarningError as ex:
            print(str(ex))

    complete_select = complete_enable
    complete_unselect = complete_disable
    do_select = do_enable
    do_unselect = do_disable


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

