# -*- coding: UTF-8 -*-
import multiprocessing
import subprocess
import time
import os

import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs
from hwd_util import *

class HWD:
	def __init__(self, startup_fname, ps_fname, check_interval, show_log_level=1):
		self.log = apr.Log(show_log_level)
		self.startup_fname = startup_fname
		self.ps_fname = ps_fname
		self.hash_startup_file_content = ''
		self.interval = check_interval
		self.cmd_map = {}
		self.pid = os.getpid()
		## $cmd_map looks like:
		## {cmd: pid}

	## Internal function
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

	def launch(self, reload_=None):
		isStartupChanged = True
		if reload_ == None:
			cmd_map_system, self.hash_startup_file_content = self.__loadStartupConfig()
		else:
			cmd_map_system = reload_[0]
			self.hash_startup_file_content = reload_[1]

		for hash_c in cmd_map_system.keys():
			## cmd_map_system[hash_c] = [pid, cmd]
			cmd_map_system[hash_c][0] = subprocess.Popen(cmd_map_system[hash_c][1], shell=True).pid
		cmd_map_system[0] = self.pid  ## Key -0 should be the main program PID
		cmd_map_system[1] = self.hash_startup_file_content  ## Key -1 should be the startup file hash
		ajs.gracefulDumpJSON(self.ps_fname, cmd_map_system)
		self.log.print(cmd_map_system, level=0)

	def daemon(self):
		## Use multiprocess in order to prevent zombie process in Linux
		l = multiprocessing.Process(target=self.launch, args=(None,))
		l.start()
		l.join()

		while True:
			time.sleep(self.interval)
			if os.path.exists(self.ps_fname) == False:
				self.log.print('Unable to launch daemon since PS file does not exist. Waiting for retry...', level=2)
			else:
				self.log.print('Daemon started.', level=1)
				break

		while True:
			cmd_map_previous = ajs.gracefulLoadJSON(self.ps_fname)
			cmd_map_current, hash_startup_file_content_current = self.__loadStartupConfig()
			if hash_startup_file_content_current != cmd_map_previous['1']:
				## Startup config changed
				self.log.print('Startup config changed. Terminate current processes.', level=2)
				l.terminate()
				terminateCurrentProcess(cmd_map_previous)
				self.log.print('Restarting...', level=1)
				l = multiprocessing.Process(target=self.launch, args=((cmd_map_current, hash_startup_file_content_current),))
				l.start()
				l.join()

			time.sleep(self.interval)