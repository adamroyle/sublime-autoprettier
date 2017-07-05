import sublime
import sublime_plugin
import os
import re
import subprocess
import shlex
import fnmatch
import time
import json

class AutoPrettier(sublime_plugin.EventListener):
	
	node_path = '/usr/local/bin/node'
	packages = {}

	def on_post_save_async(self, view):
		self.start = time.perf_counter()
		
		packages = self.get_packages(view)

		for package in packages:

			config = self.get_package(package)

			for cmd in config['commands']:
				if fnmatch.fnmatch(view.file_name(), cmd['write_path']):
					self.run_prettier(view, cmd['options'], config['prettier_path'])
					return

		print(time.perf_counter() - self.start)
		

	def globPath(self, path, root):
		return root + '/' + re.sub(r"^\./", "", path.replace('**/*', '*'))

	def run_prettier(self, view, options, prettier_path):
		cmd = [self.node_path, prettier_path] + options + ['--write', view.file_name()]
		print(cmd)
		subprocess.call(cmd)
		print(time.perf_counter() - self.start)

	def get_packages(self, view):
		packages = []
		folder = os.path.dirname(view.file_name())
		while folder != '/':
			package = folder + '/package.json'
			if os.path.exists(package):
				packages.append(package)
			folder = os.path.dirname(folder)
		return packages

	def get_package(self, path):
		mtime = os.path.getmtime(path)

		config = self.packages.get(path)

		if not config or not config.get('mtime') == mtime:
			config = self.parse_package(path)
			config['mtime'] = mtime
			self.packages[path] = config

		return config

	def parse_package(self, path):
		print('parsing package ' + path)
		jsonData = json.load(open(path, 'r'))
		
		scripts = jsonData['scripts']
		cmds = []
		root = os.path.dirname(path)

		for key in scripts:
			script = scripts[key]
			script_parts = shlex.split(script)
			
			mode = 'LOOKING_FOR_PRETTIER'
			
			for i, v in enumerate(script_parts):
				if mode == 'LOOKING_FOR_PRETTIER':
					if v == 'prettier':
						mode = 'PARSING_OPTIONS'
						options = []
				elif mode == 'PARSING_OPTIONS':
					if (v == '&&' or v == ';' or v == '|' or v == '&' or v == '||' or v == '>' or v == '>>'):
						write_path = options.pop()
						cmds.append({ 'options': options, 'write_path': self.globPath(write_path, root) })
						mode = 'LOOKING_FOR_PRETTIER'
					elif v.endswith(';'):
						v = re.sub(r";$", "", v)
						cmds.append({ 'options': options, 'write_path': self.globPath(v, root) })
						mode = 'LOOKING_FOR_PRETTIER'
					elif len(script_parts) == i + 1:
						cmds.append({ 'options': options, 'write_path': self.globPath(v, root) })
					elif v != '--write':
						options.append(v)

		return {
			'prettier_path': root + '/node_modules/.bin/prettier',
			'root': root,
			'commands': cmds
		}
