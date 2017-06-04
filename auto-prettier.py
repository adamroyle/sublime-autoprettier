import sublime
import sublime_plugin
import os
import re
import subprocess
import shlex
import fnmatch
#import time

class AutoPrettier(sublime_plugin.EventListener):
	
	node_path = '/usr/local/bin/node'
	root_path = 'asdfasdfasd'
	prettier_glob = ''
	prettier_path = ''
	prettier_options = []

	def on_post_save_async(self, view):
		#self.start = time.perf_counter()

		if not view.file_name().startswith(self.root_path):
			
			package = self.get_package_json(view)
			if package is False:
				return
			root = os.path.dirname(package)

			self.root_path = root
			
			self.prettier_path = root + '/node_modules/.bin/prettier'

			file = open(package, 'r')
			json = file.read()
			m = re.search("prettier (.+?) --write '(.+)'", json)
			file.close()
			options = m.group(1)
			glob = m.group(2)

			self.prettier_options = shlex.split(options)
			self.prettier_glob = root + '/' + glob.replace('**/*', '*')
		
		if fnmatch.fnmatch(view.file_name(), self.prettier_glob):
			self.run_prettier(view)		

	def run_prettier(self, view):
		cmd = [self.node_path, self.prettier_path] + self.prettier_options + ['--write', view.file_name()]
		#print(cmd)
		subprocess.call(cmd)
		#print(time.perf_counter() - self.start)

	def get_package_json(self, view):
		folder = os.path.dirname(view.file_name())
		while folder != '/':
			package = folder + '/package.json'
			if os.path.exists(package):
				return package
			folder = os.path.dirname(folder)
		return False
