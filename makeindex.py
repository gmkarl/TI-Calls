#!/usr/bin/env python3

import sys

from git_annex_adapter.repo import GitAnnexRepo, AnnexedFileTree, AnnexedFile
from git_annex_adapter.process import GitAnnexBatchJsonProcess

class WhereIs:
	def __init__(self, workdir):
		self.workdir = workdir
		sys.stderr.write('Loading content locations ...\n')
		self.keys = dict(self._enumerate())
		sys.stderr.write('Loaded.\n')
	def key(self, key):
		return self.keys.get(key, [])
	def _enumerate(self):
		subproc = GitAnnexBatchJsonProcess(['whereis', '--json', '--all'], self.workdir)
		while True:
			result = subproc({})
			if not result:
				break
			if 'command' in result and result['command'] == 'whereis':
				if result['success'] != True:
					raise Exception(result)
				yield (result['key'], result['whereis'])

from urllib.parse import urlparse
from xml.etree import ElementTree as ET
import sys
class Page:
	def __init__(self):
		self.html = ET.Element('html')
		self.body = ET.Element('body')
		self.html.append(self.body)
		message = ET.Element('b')
		message.text = 'These files are presently archived on the web.  I am working on storing them permanently on bsv, which costs money that I am short of and involves fixing some broken software.  If bsv is implemented it will be listed next to the files stored on it.'
		self.body.append(message)
		self.table = ET.Element('table')
		self.body.append(self.table)
	def path(self, path):
		pass
	def file(self, path, name, key, locations):
		tr = ET.Element('tr')
		self.table.append(tr)
		td = ET.Element('td')
		td.text = path + '/' + name
		tr.append(td)
		td = ET.Element('td')
		tr.append(td)
		for location in locations:
			urls = location['urls']
			if not urls:
				continue
			if not td.text:
				td.text = location['description'] + ':'
			else:
				a.tail = location['description'] + ':'
			for url in location['urls']:
				a = ET.Element('a', attrib={'href': url})
				a.text = urlparse(url).netloc
				td.append(a)
	def render(self):
		if sys.version_info < (3,0,0):
			ET.ElementTree(self.html).write(sys.stdout, encoding='utf-8', method='html')
		else:
			ET.ElementTree(self.html).write(sys.stdout, encoding='unicode', method='html')

repo = GitAnnexRepo('.')
whereiskey = WhereIs(repo.workdir).key
page = Page()

def folder(tree, path = ''):
	sys.stderr.write('Listing ' + path + '...\n')
	for name, file in tree.items():
		subpath = path + name
		if isinstance(file, AnnexedFileTree):
			folder(file, subpath + '/')
		elif isinstance(file, AnnexedFile):
			locations = whereiskey(file.key)
			page.file(path, name, file.key, locations)
folder(repo.annex.get_file_tree())
page.render()
