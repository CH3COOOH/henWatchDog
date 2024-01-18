# -*- coding: UTF-8 -*-
import sys

from hwd_util import *
import azlib.json as ajs
import hwd

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
			h = hwd.HWD(c["path_playbook"], c["path_ps"], c["check_interval"], c["log_level"])
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
