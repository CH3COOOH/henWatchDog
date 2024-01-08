# -*- coding: UTF-8 -*-
import multiprocessing
import subprocess
import time
import os
import sys

import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs

PATH_PSNOW = '/tmp/hwd_ps.json'

def terminateCurrentProcess(pid_map, suicide=False):
	for p in pid_map.keys():
		if p == '1':
			continue
		elif p == '0':
			if suicide:
				try:
					os.kill(pid_map[p], 9)
					print('%d (HWD daemon) killed.' % pid_map[p][0])
				except:
					print('Unable to kill HWD daemon. Maybe died.')
		else:
			try:
				os.kill(pid_map[p][0], 9)
				print('%d killed.' % pid_map[p][0])
			except:
				print('Unable to kill PID %d. Maybe died.' % pid_map[p][0])
	return 0

def listCurrentProcess(pid_map, diff_only=False):
	ps_cmd = 'ps'
	if diff_only == False: print('MANAGED BY HWD\n--------')
	for p in pid_map.keys():
		if p == '0':
			if diff_only == False: print('Daemon PID: %d' % pid_map[p])
			ps_cmd += ' %d' % pid_map[p]
		elif p == '1':
			if diff_only == False: print('Current startup hash: %s' % pid_map[p])
		else:
			if diff_only == False: print('%s\t%d\t%s' % (p, pid_map[p][0], pid_map[p][1]))
			ps_cmd += ' %d' % pid_map[p][0]

	ps_ex = subprocess.run(ps_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	ps_out = ps_ex.stdout.decode("utf-8")
	if diff_only == False: print('\nMANAGED BY SYSTEM\n--------\n%s--------' % ps_out)
	
	print('LOST HWD CONTROL\n--------')
	ps_out = ps_out.split('\n')[1:-1]
	ps_out = list(map(lambda x: int(x.split(' ')[0]), ps_out))
	isLost = False
	for p in pid_map.keys():
		if p == '0':
			if pid_map[p] not in ps_out:
				isLost = True
				print('[**LOST**]\tDaemon PID: %d' % pid_map[p])
		elif p != '1':
			if pid_map[p][0] not in ps_out:
				isLost = True
				print('[**LOST**]\t%d\t%s' % (pid_map[p][0], pid_map[p][1]))
	if isLost == False:
		print('All processes are under HWD control.')

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


if __name__ == '__main__':
	s_usage = '''Usage:
hwd -c <config_fname>
hwd -t <config_fname>
hwd -l <config_fname>
'''
	av = sys.argv
	if len(av) == 3:
		c = ajs.gracefulLoadJSON(av[2])
		if av[1] == '-c':
			h = HWD(c["path_playbook"], c["path_ps"], c["check_interval"], c["log_level"])
			h.daemon()
		elif av[1] == '-t':
			terminateCurrentProcess(ajs.gracefulLoadJSON(c["path_ps"]), suicide=True)
			print('Running processes killed.')
		elif av[1] == '-l':
			listCurrentProcess(ajs.gracefulLoadJSON(c["path_ps"]), True)
		elif av[1] == '-la':
			listCurrentProcess(ajs.gracefulLoadJSON(c["path_ps"]), False)
		else:
			print(s_usage)
	else:
		print(s_usage)
