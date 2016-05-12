#!/usr/bin/env python3

# Detect suspicious GIF files

import os


class Suspect(object):

	MAP = {
		'GIF image data' : 'gif',
	}
	def __init__(self, filepath, prefix):
		self._filepath = filepath
		self._prefix = prefix

	def parse(self):
		with open(self._filepath, 'rb') as tt:
			for lb in tt:
				try:
					l = str(lb, encoding='utf8').strip('\n')
				except Exception as e:
					continue
				path, type_ = l.split(':', 1)
				comps  = type_.split(',', 1)
				main = comps[0].strip()
				#print('[%s]' % main)
				if main in self.MAP:
					f = getattr(self, '_parse_%s' % self.MAP[main])
					f(path, type_)

	def _parse_gif(self, path, type_):
		main, version, format = [x.strip() for x in type_.split(',', 3)]
		w, h = map(int, format.split('x'))
		area = w * h
		if area > 4096:
			with open(os.path.join(self._prefix, path), 'rb') as gif:
				data = gif.read()
			# Adobe mess up with GIF files and add XMP data at the end of the
			# file, so discard it (hopefully a hacked will not add his crap after
			# the XML sequence...)
			pos = data.find(b'XMP ')
			if pos > 0:
				data = data[:pos]
			ratio = self.compute_ratio(data)
			if ratio >= 0.5:
				print('Suspect: %s (%.2f %%)' % (path, ratio*100))

	@staticmethod
	def compute_ratio(data):
		total = len(data)
		ascii = len([x for x in data if (x < 127) and (x >= 32)])
		return ascii/total

if __name__ == '__main__':
	s = Suspect('filetypes.txt', 'www')
	s.parse()