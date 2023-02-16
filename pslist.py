import azlib.ut as aut

class PSList:
	def __init__(self):
		self.element = ['pid', 'cmd', 'hash']
		self.process = []

	def newProcess(self, pid, cmd):
		## `p_c_h` should be a list of [pid, cmd, hash]
		hash_ = aut.str2md5(cmd)
		self.process.append([pid, cmd, hash_])

	def getProcessBy(self, byWhich, byValue):
		col_idx = self.element.index(byWhich)
		result_list = []
		for p in self.process:
			if p[col_idx] == byValue:
				result_list.append(p)
		return result_list

	def getColumnBy(self, byWhich):
		col_idx = self.element.index(byWhich)
		result_list = []
		for p in self.process:
			if p[col_idx] == byValue:
				result_list.append(p[col_idx])
		return p

	def removeProcessBy(self, byWhich, byValue):
		col_idx = self.element.index(byWhich)
		for p in self.process:
			if p[col_idx] == byValue:
				self.process.remove(p)
		return 0

	def dumps(self, isTitleContained=False):
		s = ''
		if isTitleContained:
			for col in self.element:
				s += '\t'.join(col)
			s += '\n--------\n'
		for p in self.process:
			s += ('\t'.join(p) + '\n')
		return s

	def loads(self, s_pslist):
		process = []
		for t in s_pslist.split('\n'):
			process.append(t.split('\t'))
		self.process = process.copy()
		return process




