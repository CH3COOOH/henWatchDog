# -*- coding: UTF-8 -*-

import subprocess
import time
import os

from pslist import PSList
import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs

PATH_PSNOW = '/tmp/hwd_ps.json'

class HWD:
	def __init__(self, startup_filename, check_interval, show_log_level=1):
		self.log = apr.Log(show_log_level)
		self.filename = startup_filename
		# self.startup_file_content = ''
		self.hash_startup_file_content = ''
		# self.startup_file_content_cache = ''
		# self.hash_startup_file_content_cache = ''
		self.interval = check_interval
		self.cmd_map = {}
		## $cmd_map looks like:
		## {cmd: pid}

	## Internal function
	## Will update $self.startup_file_content_cache and $self.hash_startup_file_content_cache
	## [Return]
	## cmd_map -> dict, {command: pid}
	def __loadStartupConfig(self):
		self.log.print('Loading startup config...')
		cmd_map = {}
		sCmdList = aut.gracefulRead(self.filename)
		sCmdList_hash = aut.str2md5(sCmdList)
		for c in sCmdList.split('\n'):
			if '#' in c or c == '':
				continue
			cmd_map[aut.str2md5(c)] = [-99, c]
			# [pid, cmd]
		return cmd_map, sCmdList_hash

	# ## [Return]
	# ## Startup config unchanged: False
	# ## Changed: $cmd_map_current
	# def __isStartupConfigChanged(self):
	# 	self.log.print('Checking startup config change...')
	# 	cmd_map_current = self.__loadStartupConfig()
	# 	if self.hash_startup_file_content_cache != self.hash_startup_file_content:
	# 		self.log.print('Config change detected.', level=2)
	# 		return cmd_map_current
	# 	else:
	# 		return False

	def launch(self):
		isStartupChanged = True
		cmd_map_system, self.hash_startup_file_content = self.__loadStartupConfig()

		while True:
			
			if isStartupChanged:
				## Run new process list
				cmd_map_popen = {}
				for hash_c in cmd_map_system.keys():
					## cmd_map_system[hash_c] = [pid, cmd]
					cmd_map_popen[hash_c] = subprocess.Popen(cmd_map_system[hash_c][1], shell=True)
					cmd_map_system[hash_c][0] = cmd_map_popen[hash_c].pid
				ajs.gracefulDumpJSON(PATH_PSNOW, cmd_map_system)
				self.log.print(cmd_map_system, level=0)
			
			isStartupChanged = False
			time.sleep(self.interval)

			cmd_map_current, hash_startup_file_content_current = self.__loadStartupConfig()

			## If config file change detected:
			if hash_startup_file_content_current != self.hash_startup_file_content:
				isStartupChanged = True
				for hash_c in cmd_map_popen.keys():
					cmd_map_popen[hash_c].kill()
				cmd_map_system = cmd_map_current.copy()
				self.hash_startup_file_content = hash_startup_file_content_current




		# 	## If config file change detected:
		# 	change_status = self.__isStartupConfigChanged()
		# 	if change_status != False:
		# 		self.log.print(self.cmd_map, 0)
		# 		self.log.print(change_status, 0)
		# 		for c in self.cmd_map.keys():
		# 			if c not in change_status.keys():
		# 				## Suggest that the command is removed.
		# 				self.log.print('Task removed: %s' % c, 0)
		# 				# os.kill(self.cmd_map[c], 9)
		# 				os.system('kill -9 %d' % self.cmd_map[c])
		# 				self.cmd_map[c] = -99
		# 		for c in change_status.keys():
		# 			if c not in self.cmd_map.keys():
		# 				## Suggest that new command is added.
		# 				self.log.print('New task found: %s' % c, 0)
		# 				self.cmd_map[c] = subprocess.Popen(c, shell=True).pid
		# 		self.startup_file_content = self.startup_file_content_cache
		# 		self.hash_startup_file_content = self.hash_startup_file_content_cache
		# 		ajs.gracefulDumpJSON(PATH_PSNOW, self.cmd_map)

if __name__ == '__main__':
	h = HWD('./playbook_test.txt', 10, show_log_level=0)
	h.launch()