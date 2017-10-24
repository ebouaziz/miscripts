#!/usr/bin/env python3


"""Documentation
"""

from argparse import ArgumentParser, FileType
from re import compile as recompile
from sys import exit, modules, stderr
from traceback import format_exc


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

    def __init__(self, name, options, *defwarns):
        name = name.lstrip('-').lstrip('W')
        if not name:
            raise ValueError('Warning with no name')
        self.name = name
        self.enabled = 'D' in options
        languages = [lang for lang in self.LANGUAGES if lang in options]
        if len(languages) > 1:
            raise ValueError('Too many languages: %s' % ','.join(languages))
        self.language = self.LANGUAGES[languages and languages[0] or
                                       self.DEFAULT_LANGUAGE]

    def is_lang(self, language):
        return self.language == language

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%s):%d' % (self.name, self.language, self.enabled)


class WarningChooser(object):
    """
    """

    DW_CRE = recompile(r'\(\-W([\w\-]+)\)')

    def __init__(self, language=None):
        self._warnings = {}
        self._language = Warning.LANGUAGES[language or
                                           Warning.DEFAULT_LANGUAGE]

    def load(self, fp):
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
        self.show_unselected()

    def show_unselected(self):
        warnings = [w for w in self._warnings
                    if self._warnings[w].is_lang(self._language) and
                       not self._warnings[w].enabled]
        for warn in sorted(warnings):
            print(' ', warn)
        print('%d out of %d' % (len(warnings), len(self._warnings)))


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
    except Exception as e:
        print('\nError: %s' % e, file=stderr)
        if debug:
            print(format_exc(chain=False), file=stderr)
        exit(1)
    except KeyboardInterrupt:
        exit(2)


if __name__ == '__main__':
    main()

