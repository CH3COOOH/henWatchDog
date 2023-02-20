# -*- coding: UTF-8 -*-

import subprocess
import time
import os
import sys

from pslist import PSList
import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs

PATH_PSNOW = '/tmp/hwd_ps.json'

class HWD:
	def __init__(self, startup_fname, ps_fname, check_interval, show_log_level=1):
		self.log = apr.Log(show_log_level)
		self.startup_fname = startup_fname
		self.ps_fname = ps_fname
		self.hash_startup_file_content = ''
		self.interval = check_interval
		self.cmd_map = {}
		self.self_pid = os.getpid()
		## $cmd_map looks like:
		## {cmd: pid}

	## Internal function
	## Will update $self.startup_file_content_cache and $self.hash_startup_file_content_cache
	## [Return]
	## cmd_map -> dict, {command: pid}
	def __loadStartupConfig(self):
		self.log.print('Loading startup config...')
		cmd_map = {}
		sCmdList = aut.gracefulRead(self.startup_fname)
		sCmdList_hash = aut.str2md5(sCmdList)
		for c in sCmdList.split('\n'):
			if '#' in c or c == '':
				continue
			cmd_map[aut.str2md5(c)] = [-99, c]
			# [pid, cmd]
		return cmd_map, sCmdList_hash

	def launch(self):
		isStartupChanged = True
		cmd_map_system, self.hash_startup_file_content = self.__loadStartupConfig()
		self.log.print(os.getpid(), level=0)
		self.log.print(os.getppid(), level=0)

		while True:
			
			if isStartupChanged:
				## Run new process list
				cmd_map_popen = {}
				for hash_c in cmd_map_system.keys():
					## cmd_map_system[hash_c] = [pid, cmd]
					cmd_map_popen[hash_c] = subprocess.Popen(cmd_map_system[hash_c][1], shell=True)
					cmd_map_system[hash_c][0] = cmd_map_popen[hash_c].pid
				cmd_map_system[0] = self.self_pid
				ajs.gracefulDumpJSON(self.ps_fname, cmd_map_system)
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


if __name__ == '__main__':
	h = HWD(sys.argv[1], PATH_PSNOW, 30)
	h.launch()