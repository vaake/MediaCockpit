#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2019 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#
from __init__ import _
from ServiceUtils import getService
from CutList import CutList
from Screens.MessageBox import MessageBox
from Screens.MoviePlayer import MoviePlayer
from globals import FILE_PATH


class MDCMoviePlayer(MoviePlayer):

	def __init__(self, session, filelist, fileindex, leave_quietly=False, resume=True):
		self.leave_quietly = leave_quietly
		self.fileindex = fileindex
		self.filelist = filelist
		self.downloadCuesheet = self.readCutlist
		self.current_file = self.filelist[self.fileindex]
		self.cut = None
		playservice = getService(self.current_file[FILE_PATH])
		MoviePlayer.handleLeave = self.myhandleLeave
		MoviePlayer.playNext = self.NextService
		MoviePlayer.playPrev = self.PrevService
		MoviePlayer.__init__(self, session, playservice, stopCallback=self.stopCallback, streamMode=False)
		self.skinName = ['MDCMoviePlayer', 'MoviePlayer']
		self.ENABLE_RESUME_SUPPORT = resume
		self.ALLOW_SUSPEND = True

	def NextService(self):
		MoviePlayer.leavePlayer(self)

	def PrevService(self):
		MoviePlayer.leavePlayer(self)

	def myhandleLeave(self, ask=True, _error=False):
		self.is_closing = True
		if ask and not self.leave_quietly:
			self.session.openWithCallback(self.leavePlayerConfirmed, MessageBox, _('Do you really want to stop playback?'))
		else:
			self.leavePlayerConfirmed(True)

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.close(self.fileindex)

	def isPlaying(self):
		return self.seekstate == self.SEEK_STATE_PLAY

	def getPosition(self):
		seek = self.getSeek()
		if seek is None:
			return 0
		else:
			pos = seek.getPlayPosition()
			if pos[0]:
				return 0
			return pos[1]

	def getLength(self):
		seek = self.getSeek()
		if seek is None:
			return 0
		else:
			length = seek.getLength()
			if length[0]:
				return 0
			return length[1]

	def seekTo(self, pos):
		print('MDC: Movie: seekTo: pos: %d' % pos)
		self.doSeek(pos * 90000)

	def stopCallback(self):
		self.SaveCutFile()

	def readCutlist(self):
		self.cut = CutList(self.current_file[FILE_PATH])
		if self.cut:
			self.cut_list = self.cut.getCutList()
		else:
			self.cut_list = []

	def SaveCutFile(self):
		service = self.session.nav.getCurrentService()
		if service and self.cut:
			self.cut.saveCutFile(service)
