#!/usr/bin/env python

# Turn Git diffstat output info a SVG graph to guess whose original version
# of Joomla was actually installed on an ugly web environment

import pygal

changesets = [ \
("328504b",    43),
("767f4f5",    43),
("0e20777",    42),
("9db116d",    42),
("cbf1d8d",    40),
("03b263a",    40),
("f337128",    38),
("8f783cb",    37),
("c951c59",    36),
("2a96567",    37),
("02c6bb7",    36),
("8e4340b",    37),
("335aa9c",    37),
("fa01d1d",    36),
("24cc7e8",    36),
("cda635a",    32),
("f3c5483",    35),
("e9ed987",    33),
("6652175",    32),
("b2efbec",    31),
("ca73f23",    31),
("ebc064d",    33),
("a37915e",    32),
("d691afc",    30),
("f8021a5",    29),
("d57546d",    29),
("37802c1",    29),
("310347d",    28),
("676959b",    27),
("c85aaab",    27),
("940c5c8",    24),
("d41314d",    21),
("26d9829",    17),
("6cb1926",    13),
("1f4a210",    12),
("b4e3ae1",    10),
("03b76c0",     9),
("3d4830c",     8),
("9563e1d",     7),
("aceda8e",     6),
("2492c95",     5),
("6a392f9",     7),
("4573316",     4),
("8b4a572",     4),
("6ac8653",     3),
("9b890a1",     2),
("1209ce2",     5),
("4c0833d",     3),
("a5385be",     4),
("1dacceb",     4),
("64ae089",     5),
("3a0f0d8",     5),
("ac2a16c",     6),
("340792f",     7),
("117c16f",     8),
("32dd322",     9),
("ad4ecb5",    17),
("935de65",    10),
("701aacf",    13),
("3bf4504",    17),
("1bade03",    18),
("e6f3c81",    18),
("b1099e5",    20),
("8549b10",    19),
("d9473f0",    21),
("b190b83",    21),
("860f90d",    21),
("4fa255d",    21),
("b175c9f",    34),
("112fe6a",    21),
("b39587d",    22),
("fab65fa",    24),
("2c8ec1c",    26),
("9b23b0b",    29),
("403c71d",    29),
("c485a11",    31),
("df898ba",    34),
("af16059",    36),
("19be82f",    37),
("229041d",    37),
("dc78dee",    38),
("a76056a",    40),
("53dfd46",    41),
("dfe1a2a",    41),
("11ec25d",    43),
("6d273fe",    44),
("57c54ef",    49),
("5049663",    49),
("9ccb500",    52),
("4d8f234",    52),
("1d73a1e",    52),
("81831e6",    54),
("53056b2",    66),
("7838cd9",    67),
("b6ea7e2",    55),
("3057290",    56),
("12f69bc",    57),
("7ceacb2",    58),
("099533b",    58),
("62760ae",    63),
("ed472ef",    64),
("949bc53",    60),
("8bf5b8a",    60),
("1fb27f2",    65),
("0e3935e",    65),
("3841b3d",    65),
("5ec4633",    65),
("27b6c3b",    65),
("d5f36e9",    65),
("dcd49c4",    66),
("f71d608",    67),
("e1be791",    69),
("0a15770",    67),
("71666ad6",   67),
("8fb4dbb",    65),
("8d4a08e",    69),
("d843b2d",    69),
("c3bdcc2",    70),
("b9cbc19",    70),
("4bc04ca",    71),
("7f7a02e",    71),
("dc7513b",    71),
("3a497f5",    66),
("b5181cc",    71),
("1b06ed8",    71),
("19811e7",    71),
("8e13ac1",    66),
("12078b5",    66),
("2305ab3",    65),
("d703d97",    66),
("a4853fa",    73),
("b6877dd",    66),
("6a13f13",    67),
("42745fb",    66),
("d15eb4d",    66),
("286318f",    66),
("4543708",    67),
("3ea161d",    67),
("008cbab",    67),
("c1e795e",    67),
("b13cbfe",    67),
("d4e7cb7",    68),
("2433e1a",    67),
("9009b52",    73),
("21bdc36",    68),
("3f359fb",    68),
("c13d05e",    68),
("3ba17e0",    70),
("247b34d",    70),
("f5f5a76",    71),
("5baf049",    73),
("e291dd1",    73),
("eb98177",    74)]

changesets = (\
("2.5.14",      60),
("2.5.13",      58),
("2.5.12",      58),
("2.5.11",       5),
("2.5.10",      13),
("2.5.9",       76), 
("2.5.8",     1947),
("2.5.7",     1951),
("2.5.6",     1967),
("2.5.5",     1970),
("2.5.4",     2034),
("2.5.3",     2032),
("2.5.2",     2031),
("2.5.1",     2031),
)

#chart = pygal.Pyramid(human_readable=True, legend_at_bottom=True)
chart = pygal.HorizontalStackedBar()
chart.title = 'Delta Joomla <-> Apchea'
chart.x_labels = [c[0] for c in changesets]
#for c in changesets:
chart.add('', [c[1] for c in changesets])
chart.render_to_file('changes_joomla.svg')
