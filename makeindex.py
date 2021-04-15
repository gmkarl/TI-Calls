#!/usr/bin/env python3

from datetime import datetime
import dateutil.parser
import sys

import re

import requests

from git_annex_adapter.repo import GitAnnexRepo, AnnexedFileTree, AnnexedFile
from git_annex_adapter.process import GitAnnexBatchJsonProcess, Process

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
                    result['command'] = 'whereis --json --all'
					raise Exception(result, "This may be due to a git-annex remote error that displays only for this command line.")
				yield (result['key'], result['whereis'])
class GitLog:
	def __init__(self, workdir):
		self.workdir = workdir
	def file(self, path):
		with Process(['git', 'log', '--oneline', '--no-abbrev-commit', path], self.workdir) as subproc:
			while True:
				line = subproc.readline(timeout = None)
				if not line:
					break
				commit, log = line.split(' ', 1)
				yield commit
			

from urllib.parse import urlparse
from xml.etree import ElementTree as ET
import sys
class Page:
	def __init__(self):
		self.html = ET.Element('html')
		self.head = ET.Element('head')
		self.html.append(self.head)
		self.body = ET.Element('body')
		self.html.append(self.body)
		message = ET.Element('b')
		message.text = 'The files linked below are presently archived on the web.  I am working on storing them permanently on bsv, which costs money that I am short of and involves fixing some broken software.  If bsv is implemented it will be listed next to the files that are stored on it, on a future version of this page.'
		paragraph = ET.Element('p')
		paragraph.append(message)
		self.body.append(paragraph)
		paragraph = ET.Element('p')
		paragraph.text = 'This web address likely identifies this specific version of this page, and a new web address will be needed to find new versions.'
		self.body.append(paragraph)
		paragraph = ET.Element('p')
		paragraph.text = 'Until we get bsv working again, most of the mirrors below are "skynet" mirrors so far, which are offering free storage.  These seem to work well but do not guarantee preservation of content and are all linked into the same one network.'
		self.body.append(paragraph)
		paragraph = ET.Element('p')
		paragraph.text = 'If you are familiar with git-annex, the contents of this repository are the last file at the bottom.  You will want the one with the most recent date.'
		self.body.append(paragraph)
		self.table = ET.Element('table')
		self.body.append(self.table)
		self.files = {}
	def urlgood(self, url):
		try:
			response = requests.head(url, timeout=1)
			return response.ok
		except requests.exceptions.RequestException:
			return False
	def file(self, path, name, date, key, locations):
		tr = ET.Element('tr')
		namedate = re.search('\d\d\d+-\d+-\d+-\d+:\d+:\d+', name)
		if namedate:
			namedate = name[namedate.start():namedate.end()]
			namedate = dateutil.parser.parse(namedate).isoformat()
		if not namedate:
			namedate = name
		if not namedate in self.files:
			self.files[namedate] = []
		self.files[namedate].append(tr)
		td = ET.Element('td')
		td.text = path + name
		tr.append(td)
		td = ET.Element('td')
		td.text = date.isoformat()
		tr.append(td)
		td = ET.Element('td')
		td.text = ''
		tr.append(td)
		lastelem = None
		for location in locations:
			urls = location['urls']
			if not urls:
				continue
			count = 0
			for url in location['urls']:
				if url[0:4] != 'http':# or not self.urlgood(url):
					continue
				count += 1
				a = ET.Element('a', attrib={'href': url})
				a.text = urlparse(url).netloc
				a.tail = ' '
				td.append(a)
				lastelem = a
			if count == 0:
				continue
			if not td.text:
				td.text += location['description'] + ':'
			else:
				lastelem.tail += location['description'] + ':'
	def render(self):
		for filename in sorted(self.files, reverse=True):
			for version in self.files[filename]:
				self.table.append(version)
		if sys.version_info < (3,0,0):
			ET.ElementTree(self.html).write(sys.stdout, encoding='utf-8', method='html')
		else:
			ET.ElementTree(self.html).write(sys.stdout, encoding='unicode', method='html')

class CallRepo:
	def __init__(self, workdir = '.'):
		self.repo = GitAnnexRepo(workdir)
		self.whereiskey = WhereIs(workdir).key
		self.gitlogfile = GitLog(workdir).file
		self.page = Page()
	def process(self):
		self._folder(self.repo.annex.get_file_tree())
		self.page.render()
	def _file(self, path, name, file):
		commits = []
		for commit in self.gitlogfile(path + name):
			timestamp = self.repo[commit].commit_time
			date = datetime.utcfromtimestamp(timestamp)
			file = self.repo.annex.get_file_tree(commit)[path + name]
			# replace duplicates [todo: don't even store this in the commit history]
			while len(commits) and (
					commits[-1]['file'].key[:5] == 'URL--' or
					commits[-1]['file'].key == file.key
				):
				commits.pop()
			if len(commits) and file.key[:5] == 'URL--':
				commits[0]['extra'] = file
			else:
				commits.append({'commit':commit, 'timestamp':timestamp, 'date':date, 'file':file})
		for commit in commits:
			sys.stderr.write(path +  name + ' ' + commit['file'].key + '\n')
			locations = self.whereiskey(commit['file'].key)
			if 'extra' in commit:
				locations.extend(self.whereiskey(commit['extra'].key))
			self.page.file(path, name, commit['date'], commit['file'].key, locations)
	def _folder(self, tree, path = ''):
		sys.stderr.write('Listing ' + path + '...\n')
		for name, file in tree.items():
			if isinstance(file, AnnexedFileTree):
				self._folder(file, path + name + '/')
			elif isinstance(file, AnnexedFile):
				self._file(path, name, file)

CallRepo().process()
