import os
import struct
from bisect import insort

class CutList(object):
	CUT_TYPE_IN = 0
	CUT_TYPE_OUT = 1
	CUT_TYPE_MARK = 2
	CUT_TYPE_LAST = 3
	CUT_TYPE_SAVEDLAST = 4

	def __init__(self, path=None):
		self.cut_file = path + '.cuts'
		self.cut_mtime = 0
		self.cut_list = []
		self.__readCutFile()

	def __insort(self, pts, what):
		if (pts, what) not in self.cut_list:
			insort(self.cut_list, (pts, what))

	def getCutList(self):
		return self.cut_list

	def getCutListMTime(self):
		return self.cut_mtime

	def getCutListLast(self):
		return self.__ptsToSeconds(self.__getCutListLast())

	def getCutListLength(self):
		return self.__ptsToSeconds(self.__getCutListLength())

	def __ptsToSeconds(self, pts):
		return pts / 90 / 1000

	def __getCutListLast(self):
		if self.cut_list:
			for pts, what in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					return pts
		return 0

	def __getCutListLength(self):
		if self.cut_list:
			for pts, what in self.cut_list:
				if what == self.CUT_TYPE_OUT:
					return pts
		return 0

	def __getCutListSavedLast(self):
		if self.cut_list:
			for pts, what in self.cut_list:
				if what == self.CUT_TYPE_SAVEDLAST:
					return pts
		return 0

	def __removeSavedLast(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[0] == pts:
					if cp[1] == self.CUT_TYPE_SAVEDLAST:
						self.cut_list.remove(cp)

	def __replaceLast(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] == self.CUT_TYPE_LAST:
					self.cut_list.remove(cp)
		if pts > 0:
			self.__insort(pts, self.CUT_TYPE_LAST)
		return

	def __replaceOut(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] == self.CUT_TYPE_OUT:
					self.cut_list.remove(cp)
		if pts > 0:
			self.__insort(pts, self.CUT_TYPE_OUT)
		return

	def saveCutFile(self, service):
		currPos = 0
		length = 0
		seek = service.seek()
		if seek:
			tmppos = seek.getPlayPosition()
			if isinstance(tmppos, list) and tmppos[0] == 0 and tmppos[1] > 0:
				currPos = int(tmppos[1])
			tmplen = seek.getLength()
			if isinstance(tmplen, list) and tmplen[0] == 0 and tmplen[1] > 0:
				length = int(tmplen[1])
		self.__removeSavedLast(self.__getCutListSavedLast())
		self.__replaceLast(currPos)
		self.__replaceOut(length)
		if len(self.cut_list) > 1:
			try:
				data = ''
				for pts, what in self.cut_list:
					data += struct.pack('>QI', pts, what)

				if data:
					with open(self.cut_file, 'wb') as cfile:
						cfile.write(data)
			except Exception as e:
				print('MDC: [%s] <%s>' % (__name__, e))

	def __readCutFile(self):
		self.cut_list = []
		if os.path.exists(self.cut_file):
			data = ''
			mtime = os.path.getmtime(self.cut_file)
			if self.cut_mtime == mtime:
				pass
			else:
				self.cut_mtime = mtime
				f = None
				try:
					f = open(self.cut_file, 'rb')
					data = f.read()
				except Exception as e:
					print('MDC: __[%s] <%s>' % (__name__, e))
				finally:
					if f is not None:
						f.close()
				if data:
					pos = 0
					while pos + 12 <= len(data):
						pts, what = struct.unpack('>QI', data[pos:pos + 12])
						self.__insort(int(pts), what)
						pos += 12
		return
