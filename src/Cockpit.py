#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2019 by dream-alpha
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
import os
from __init__ import _
from PictureUtils import setThumbPixmap, setFullPixmap
from Movie import MDCMoviePlayer
from ConfigScreen import ConfigScreen
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.LocationBox import LocationBox
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from Components.config import config
from enigma import eSize, ePoint, gFont, ePicLoad, getDesktop
from Picture import MDCPicturePlayer
from PictureUtils import rotatePictureExif
from FileUtils import deleteFile
from globals import FILE_FILTER, FILE_PATH, FILE_TYPE, FILE_META, FILTER_DIR, FILTER_FILE, FILTER_GOUP
from FileListUtils import scanDirectory, createGoupEntry, scanPlaylist
from FileInfo import FileInfo
from SkinUtils import getSkinPath
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor


class MDCSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		self.skinName = ['MDCSummary']


class Cockpit(Screen, HelpableScreen):

	def __init__(self, session):
		print("MDC-I: Cockpit: __init__")
		self.tile_columns = 5
		self.tile_rows = 3
		self.tiles = self.tile_columns * self.tile_rows
		self.sc = AVSwitch().getFramebufferScale()
		self.picLoads = {}
		self.skinName = self.getSkinName()

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self,
			"MDCActions",
			{
				'nextBouquet':	(self.PrevPage,		_('Previous page')),
				'prevBouquet':	(self.NextPage,		_('Next page')),
				'right':	(self.KeyRight,		_('Next picture')),
				'left':		(self.KeyLeft,		_('Previous picture')),
				'up':		(self.KeyUp,		_('Previous line')),
				'down':		(self.KeyDown,		_('Next line')),
				'green':	(self.KeyOk,		_('Ok')),
				'ok':		(self.KeyOk,		_('Ok')),
				'info':		(self.KeyInfo,		_('Information')),
				'menu':		(self.KeyMenu,		_('Settings')),
				'red':		(self.KeyExit,		_('Exit')),
				'exit':		(self.KeyExit,		_('Exit')),
				'0':		(self.Key0,		_('Home')),
			},
			prio=-1
		)

		self["no_support"] = Label(_("Skin resolution other than Full HD is not supported yet"))
		self['Infobar'] = Label()
		self['lcdinfo'] = StaticText()
		self['title'] = StaticText()

		for tile_pos in range(self.tiles):
			self['BGFrame%d' % tile_pos] = Label()
			self['BGFrame%d' % tile_pos].hide()
			self['BGLabel%d' % tile_pos] = Label()
			self['Picture%d' % tile_pos] = Pixmap()
			self['TXLabel%d' % tile_pos] = Label()

		if config.plugins.mediacockpit.start_home_dir.value:
			self.last_path = config.plugins.mediacockpit.home_dir.value
		else:
			self.last_path = config.plugins.mediacockpit.last_path.value
		print("MDC-I: Cockpit: __init__: last_path: %s" % self.last_path)

		self.first_start = True
		self.onShow.append(self.onDialogShow)

	def createSummary(self):
		return MDCSummary

	def onDialogShow(self):
		#print("MDC: Cockpit: onDialogShow")
		if self.first_start:
			self.firstStart()
			self.first_start = False

	def getSkinName(self):
		width = getDesktop(0).size().width()
		if width == 1920:
			skinName = "Cockpit"
		else:
			skinName = "MDCNoSupport"
			self.setTitle(_("Information"))
		return skinName

	def firstStart(self):
		#print("MDC: Cockpit: firstStart: first_start: %s" % self.first_start)
		self.filelist_skip_system_files = config.plugins.mediacockpit.skip_system_files.value
		self.filelist_sort = config.plugins.mediacockpit.sort.value
		self.selection_size_offset = config.plugins.mediacockpit.selection_size_offset.value
		self.selection_font_offset = config.plugins.mediacockpit.selection_font_offset.value
		self.normal_background_color = parseColor(config.plugins.mediacockpit.normal_background_color.value)
		self.selection_background_color = parseColor(config.plugins.mediacockpit.selection_background_color.value)
		self.normal_foreground_color = parseColor(config.plugins.mediacockpit.normal_foreground_color.value)
		self.selection_foreground_color = parseColor(config.plugins.mediacockpit.selection_foreground_color.value)
		self.selection_frame_color = parseColor(config.plugins.mediacockpit.selection_frame_color.value)

		for tile_pos in range(self.tiles):
			self['BGFrame%d' % tile_pos].instance.setBackgroundColor(self.selection_frame_color)
			self['BGLabel%d' % tile_pos].instance.setForegroundColor(self.normal_foreground_color)
			self['BGLabel%d' % tile_pos].instance.setBackgroundColor(self.normal_background_color)
			self['TXLabel%d' % tile_pos].instance.setForegroundColor(self.normal_foreground_color)
			self['TXLabel%d' % tile_pos].instance.setBackgroundColor(self.normal_background_color)

		font = self['TXLabel0'].instance.getFont()
		self.font_family = font.family
		self.font_size = font.pointSize

		self.scale_size = self['Picture0'].instance.size()

		next_path = self.last_path
		ext = os.path.splitext(next_path)[1]
		if ext and ext != ".m3u":
			next_path = os.path.dirname(next_path)
		self.current_path = ""
		self.readFileList(next_path)

		if self.first_start and config.plugins.mediacockpit.stop_tv_playback.value:
			#print("MDC: Cockpit: firstStart: clear video buffer")
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()
			self.session.nav.playService(self.lastservice)
			self.session.nav.stopService()

	def selectTile(self, tile_pos):
		print("MDC-I: Cockpit: selectTile: tile_pos: %s" % tile_pos)
		if config.plugins.mediacockpit.frame.value:
			self['BGFrame%d' % tile_pos].show()
		size = self['BGFrame%d' % tile_pos].instance.size()
		pos = self['BGFrame%d' % tile_pos].instance.position()
		self['BGFrame%d' % tile_pos].instance.resize(eSize(size.width() + self.selection_size_offset * 2, size.height() + self.selection_size_offset * 2))
		self['BGFrame%d' % tile_pos].instance.move(ePoint(pos.x() - self.selection_size_offset, pos.y() - self.selection_size_offset))
		size = self['BGLabel%d' % tile_pos].instance.size()
		pos = self['BGLabel%d' % tile_pos].instance.position()
		self['BGLabel%d' % tile_pos].instance.resize(eSize(size.width() + self.selection_size_offset * 2, size.height() + self.selection_size_offset * 2))
		self['BGLabel%d' % tile_pos].instance.move(ePoint(pos.x() - self.selection_size_offset, pos.y() - self.selection_size_offset))
		self['BGLabel%d' % tile_pos].instance.setBackgroundColor(self.selection_background_color)
		self['BGLabel%d' % tile_pos].instance.setForegroundColor(self.selection_foreground_color)
		size = self['Picture%d' % tile_pos].instance.size()
		pos = self['Picture%d' % tile_pos].instance.position()
		self['Picture%d' % tile_pos].instance.resize(eSize(size.width() + self.selection_size_offset * 2, size.height() + self.selection_size_offset * 2))
		self['Picture%d' % tile_pos].instance.move(ePoint(pos.x() - self.selection_size_offset, pos.y() - self.selection_size_offset))
		size = self['TXLabel%d' % tile_pos].instance.size()
		pos = self['TXLabel%d' % tile_pos].instance.position()
		self['TXLabel%d' % tile_pos].instance.resize(eSize(size.width() + self.selection_size_offset * 2, size.height()))
		self['TXLabel%d' % tile_pos].instance.move(ePoint(pos.x() - self.selection_size_offset, pos.y() + self.selection_size_offset))
		self['TXLabel%d' % tile_pos].instance.setFont(gFont(self.font_family, self.font_size + self.selection_font_offset))
		self['TXLabel%d' % tile_pos].instance.setBackgroundColor(self.selection_background_color)
		self['TXLabel%d' % tile_pos].instance.setForegroundColor(self.selection_foreground_color)

	def unselectTile(self, tile_pos):
		print("MDC-I: Cockpit: unselectTile: tile_pos: %s" % tile_pos)
		if tile_pos >= 0:
			self['BGFrame%d' % tile_pos].hide()
			size = self['BGFrame%d' % tile_pos].instance.size()
			pos = self['BGFrame%d' % tile_pos].instance.position()
			self['BGFrame%d' % tile_pos].instance.resize(eSize(size.width() - self.selection_size_offset * 2, size.height() - self.selection_size_offset * 2))
			self['BGFrame%d' % tile_pos].instance.move(ePoint(pos.x() + self.selection_size_offset, pos.y() + self.selection_size_offset))
			size = self['BGLabel%d' % tile_pos].instance.size()
			pos = self['BGLabel%d' % tile_pos].instance.position()
			self['BGLabel%d' % tile_pos].instance.resize(eSize(size.width() - self.selection_size_offset * 2, size.height() - self.selection_size_offset * 2))
			self['BGLabel%d' % tile_pos].instance.move(ePoint(pos.x() + self.selection_size_offset, pos.y() + self.selection_size_offset))
			self['BGLabel%d' % tile_pos].instance.setBackgroundColor(self.normal_background_color)
			self['BGLabel%d' % tile_pos].instance.setForegroundColor(self.normal_foreground_color)
			size = self['Picture%d' % tile_pos].instance.size()
			pos = self['Picture%d' % tile_pos].instance.position()
			self['Picture%d' % tile_pos].instance.resize(eSize(size.width() - self.selection_size_offset * 2, size.height() - self.selection_size_offset * 2))
			self['Picture%d' % tile_pos].instance.move(ePoint(pos.x() + self.selection_size_offset, pos.y() + self.selection_size_offset))
			size = self['TXLabel%d' % tile_pos].instance.size()
			pos = self['TXLabel%d' % tile_pos].instance.position()
			self['TXLabel%d' % tile_pos].instance.resize(eSize(size.width() - self.selection_size_offset * 2, size.height()))
			self['TXLabel%d' % tile_pos].instance.move(ePoint(pos.x() + self.selection_size_offset, pos.y() - self.selection_size_offset))
			self['TXLabel%d' % tile_pos].instance.setFont(gFont(self.font_family, self.font_size))
			self['TXLabel%d' % tile_pos].instance.setBackgroundColor(self.normal_background_color)
			self['TXLabel%d' % tile_pos].instance.setForegroundColor(self.normal_foreground_color)

	def readFileList(self, next_path):
		print("MDC-I: Cockpit: readFileList: next_path: %s, last_path: %s" % (next_path, self.last_path))
		self.last_tile_pos = -1
		self.current_page = -1
		self.fileindex = -1
		self.picLoads.clear()

		self.filelist = []

		x = createGoupEntry(next_path)
		if x is not None:
			self.filelist.append(x)
		if os.path.splitext(next_path)[1] == ".m3u":
			self.filelist += scanPlaylist(next_path, self.filelist_sort)
		else:
			self.filelist += scanDirectory(next_path, sort=self.filelist_sort, skip_system_files=False, onlyfiles=True, filefilters=['playlist'])
			self.filelist += scanDirectory(next_path, sort=self.filelist_sort, skip_system_files=False, filefilters=['picture', 'movie'])
		self.current_path = next_path

		if self.filelist:
			#print("MDC: Cockpit: readFileList: self.filelist: %s" % str(self.filelist))
			self.fileindex = 0
			for index, x in enumerate(self.filelist):
				#print("MDC: Cockpit: readFileList: x: %s, last_path: %s" % (str(x), self.last_path))
				if x[FILE_PATH] == self.last_path:
					self.fileindex = index
		self.last_path = self.current_path

		#print("MDC: Cockpit: readFile: fileindex: %s" % self.fileindex)
		if self.fileindex > -1:
			self.paintFrame()
		else:
			self.readFileList(config.plugins.mediacockpit.last_path.value)

	def selectDirectory(self, callback, title, current_dir):
		self.session.openWithCallback(
			callback,
			LocationBox,
			windowTitle=title,
			text=_("Select directory"),
			currDir=current_dir,
			bookmarks=config.plugins.mediacockpit.mediadirs,
			autoAdd=False,
			editDir=True,
			inhibitDirs=["/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"],
			minFree=100
		)

	def paintFrame(self, force=False):
		print("MDC-I: Cockpit: paintFrame: current_page: %s, fileindex: %s" % (self.current_page, self.fileindex))
		page = self.fileindex / self.tiles
		if page != self.current_page or force:
			self.picLoads.clear()
			self.current_page = page
			first_idx = self.current_page * self.tiles
			last_idx = (self.current_page + 1) * self.tiles
			#print("MDC: Cockpit: paintFrame: first_idx: %s, last_idx: %s" % (first_idx, last_idx))
			for idx in range(first_idx, last_idx):
				tile_pos = idx % self.tiles
				if idx < len(self.filelist):
					self['Picture%d' % tile_pos].hide()
					self['TXLabel%d' % tile_pos].setText(os.path.basename(self.filelist[idx][FILE_PATH]))
					self['TXLabel%d' % tile_pos].show()
					self['BGLabel%d' % tile_pos].show()
					self.showIcon(idx)
					if self.filelist[idx][FILE_TYPE] == 'picture':
						self.showThumbnail(idx)
				else:
					self['BGLabel%d' % tile_pos].hide()
					self['Picture%d' % tile_pos].hide()
					self['TXLabel%d' % tile_pos].hide()
					self['BGFrame%d' % tile_pos].hide()

		tile_pos = self.fileindex % self.tiles
		#print("MDC: Cockpit: paintFrame: tile_pos: %s, last_tile_pos: %s" % (tile_pos, self.last_tile_pos))

		if tile_pos != self.last_tile_pos:
			self.selectTile(tile_pos)
			self.unselectTile(self.last_tile_pos)
		self.last_tile_pos = tile_pos

		x = self.filelist[self.fileindex]
		path = x[FILE_PATH]
		pagestr = "%s: %d/%d" % (_("Page"), self.current_page + 1, len(self.filelist) / self.tiles + 1)

		self['title'].setText(pagestr)
		self['lcdinfo'].setText(os.path.basename(path))

		if x[FILE_FILTER] & FILTER_FILE:
			self['Infobar'].setText('%s - %s: %s' % (pagestr, _('File'), path))
		elif x[FILE_FILTER] & FILTER_GOUP:
			path = self.last_path
			if os.path.splitext(self.last_path)[1] != ".m3u":
				path = os.path.dirname(self.last_path)
			self['Infobar'].setText('%s - %s: %s' % (pagestr, _('Path'), path))
		elif x[FILE_FILTER] & FILTER_DIR:
			self['Infobar'].setText('%s - %s: %s' % (pagestr, _('Path'), path))

	def showIcon(self, idx):
		x = self.filelist[idx]
		#print("MDC: Cockpit: showIcon: idx: %s, x: %s" % (idx, (str(x))))
		tile_pos = idx % self.tiles
		ptr = LoadPixmap(path=getSkinPath("images/" + x[FILE_TYPE] + ".svg"), cached=False)
		if ptr:
			setThumbPixmap(self['Picture%d' % tile_pos], ptr)
			self['Picture%d' % tile_pos].show()

	def showThumbnail(self, idx):
		#print("MDC: Cockpit: showThumbnail: idx: %s" % idx)
		tile_pos = idx % self.tiles
		page = idx / self.tiles
		if tile_pos in self.picLoads:
			self['Picture%d' % tile_pos].show()
		else:
			path = self.filelist[idx][FILE_PATH]
			if config.plugins.mediacockpit.rotate.value:
				meta_data = self.filelist[idx][FILE_META]
				path = rotatePictureExif(path, meta_data)
			ext = os.path.splitext(path)[1]
			setJPEG = 2 if ext == '.jpg' or ext == '.jpeg' else 1
			size = self.scale_size
			self.picLoads[tile_pos] = ePicLoad()
			self.picLoads[tile_pos].conn = self.picLoads[tile_pos].PictureData.connect(boundFunction(self.showThumbnailCallback, page, tile_pos))
			#print("MDC: Cockpit: showThumbnail: setPara: size.width: %s, size.height: %s, sc0: %s, sc1: %s, setJPEG: %s" % (size.width(), size.height(), self.sc[0], self.sc[1], setJPEG))
			self.picLoads[tile_pos].setPara((size.width(), size.height(), self.sc[0], self.sc[1], 0, setJPEG, 'background'))
			self.picLoads[tile_pos].getThumbnail(path)

	def showThumbnailCallback(self, page, tile_pos, _info):
		#print("MDC: Cockpit: showThumbnailCallback: current_page: %s, page: %s, tile_pos: %s" % (self.current_page, page, tile_pos))
		ptr = self.picLoads[tile_pos].getData()
		if ptr:
			if page == self.current_page:
				setFullPixmap(self['Picture%d' % tile_pos], ptr, self.scale_size, eSize(self.sc[0], self.sc[1]))
				self['Picture%d' % tile_pos].show()

	def setFrameIndex(self, val=None, _val1=None, _val2=None):
		if val is not None:
			self.fileindex = val
			self.paintFrame()

	def KeyExit(self):
		self.picLoads.clear()
		if self.filelist:
			path = self.filelist[self.fileindex][FILE_PATH]
			if self.filelist[self.fileindex][FILE_FILTER] & FILTER_GOUP:
				path = os.path.dirname(self.current_path)
			config.plugins.mediacockpit.last_path.value = path
		config.plugins.mediacockpit.save()
		if config.plugins.mediacockpit.stop_tv_playback.value:
			self.session.nav.playService(self.lastservice)
		self.close()

	def Key0(self):
		self.fileindex = 0
		self.paintFrame()

	def KeyLeft(self):
		self.fileindex -= 1
		if self.fileindex < 0:
			self.fileindex = len(self.filelist) - 1
		self.paintFrame()

	def KeyRight(self):
		self.fileindex += 1
		if self.fileindex > len(self.filelist) - 1:
			self.fileindex = 0
		self.paintFrame()

	def KeyUp(self):
		self.fileindex -= self.tile_columns
		if self.fileindex < 0:
			self.fileindex = len(self.filelist) - 1
		self.paintFrame()

	def KeyDown(self):
		self.fileindex += self.tile_columns
		if self.fileindex > len(self.filelist) - 1:
			self.fileindex = 0
		self.paintFrame()

	def NextPage(self):
		self.fileindex += self.tiles
		self.fileindex = self.fileindex / self.tiles * self.tiles
		if self.fileindex > len(self.filelist) - 1:
			self.fileindex = 0
		self.paintFrame()

	def PrevPage(self):
		self.fileindex -= self.tiles
		if self.fileindex < 0:
			self.fileindex = len(self.filelist) - 1
		self.fileindex = self.fileindex / self.tiles * self.tiles
		self.paintFrame()

	def KeyOk(self):
		#print("MDC: Cockpit: KeyOk")
		x = self.filelist[self.fileindex]
		if x[FILE_FILTER] & FILTER_DIR:
			self.unselectTile(self.last_tile_pos)
			self.readFileList(x[FILE_PATH])
		elif x[FILE_FILTER] & FILTER_FILE:
			if x[FILE_TYPE] == 'playlist':
				self.unselectTile(self.last_tile_pos)
				self.readFileList(x[FILE_PATH])
			elif x[FILE_TYPE] == 'picture':
				self.session.openWithCallback(self.setFrameIndex, MDCPicturePlayer, self.filelist, self.fileindex)
			elif x[FILE_TYPE] == 'movie':
				self.session.openWithCallback(self.setFrameIndex, MDCMoviePlayer, self.filelist, self.fileindex)

	def KeyInfo(self):
		if self.filelist:
			x = self.filelist[self.fileindex]
			if x[FILE_FILTER] & FILTER_FILE:
				self.session.openWithCallback(self.setFrameIndex, FileInfo, self.filelist, self.fileindex)

	def KeyMenu(self):
		menu = []
		if self.filelist:
			menu.append((_('Delete'), 'delete', self.filelist[self.fileindex]))
		menu.append((_('Settings'), 'settings', None))
		self.session.openWithCallback(self.KeyMenuCallback, ChoiceBox, list=menu)

	def KeyMenuCallback(self, what=None):
		if what:
			if what[1] == 'delete':
				self.session.openWithCallback(self.queryDeleteCallback, MessageBox, _('Do you really want to delete the file?'))
			elif what[1] == 'settings':
				self.session.openWithCallback(self.ConfigScreenCallback, ConfigScreen)

	def ConfigScreenCallback(self, _restart=False):
		self.unselectTile(self.last_tile_pos)
		self.firstStart()

	def queryDeleteCallback(self, ok=None):
		if ok:
			deleteFile(self.filelist[self.fileindex][FILE_PATH])
			self.unselectTile(self.last_tile_pos)
			self.fileindex -= 1
			if self.fileindex < 0:
				self.fileindex = len(self.filelist) - 1
			self.last_path = self.filelist[self.fileindex][FILE_PATH]
			self.readFileList(self.current_path)
