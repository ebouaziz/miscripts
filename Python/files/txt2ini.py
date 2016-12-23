#!/usr/bin/env python3

from codecs import BOM_UTF8
from jinja2 import Environment, FileSystemLoader, Template
from os.path import abspath
from re import compile as recompile
from sys import argv


class Text2Ini(object):
    """
    """

    QCRE = recompile(r'^(?P<qn>\d+)\.\s+(?P<start>.*?)(\s{4,})(?P<end>.*)$')
    ACRE = recompile(r'[a-z]\)([\s\w\'"]+)(?!\))')

    def __init__(self):
        self._titles = []
        self._qas = []

    def parse(self, fp):
        for ln, line in enumerate(fp, start=1):
            line = line.strip().replace('’', "'")
            if ln == 1 and line.encode().startswith(BOM_UTF8):
                continue
            if not line:
                continue
            qmo = self.QCRE.match(line)
            if qmo:
                self._qas.append(qmo.groupdict())
                # print("Q:", qmo.groups())
                continue
            amos = self.ACRE.findall(line)
            if amos:
                answers = [amo.strip() for amo in amos]
                count = len(answers)
                self._qas[-1].update({'answers': answers,
                                      'count': count})
                # print("  %d: '%s'" % (an, amo.strip()))
                continue
            if self._qas:
                raise ValueError("Unknown line @ %d:'%s'" % (ln, line))
            else:
                self._titles.append(line)

    def show(self):
        from pprint import pprint
        pprint(self._qas)

    def generate(self):
        latex_jinja_env = Environment(
            block_start_string='\BLOCK{',
            block_end_string='}',
            variable_start_string='\VAR{',
            variable_end_string='}',
            comment_start_string='\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            loader=FileSystemLoader(abspath('.'))
        )
        template = latex_jinja_env.get_template('qcm.tex')
        print(template.render(title=self._titles[0],
                              questions=self._qas))


def main():
    t2i = Text2Ini()
    with open(argv[1], 'rt') as infp:
        t2i.parse(infp)
    # t2i.show()
    t2i.generate()


if __name__ == '__main__':
    main()
