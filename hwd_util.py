# -*- coding: UTF-8 -*-
import os
import subprocess

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
	ps_out = list(map(lambda x: int(x.strip().split(' ')[0]), ps_out))
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