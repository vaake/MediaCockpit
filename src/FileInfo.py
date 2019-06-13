#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2019 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      For more information on the GNU General Public License see:
#      <http://www.gnu.org/licenses/>.
#
from __init__ import _
from enigma import ePicLoad
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.Sources.List import List
from Components.ActionMap import HelpableActionMap
from globals import FILE_DATE, FILE_PATH, FILE_TYPE, FILE_META
from PictureUtils import rotatePictureExif
from datetime import datetime
from SkinUtils import getSkinPath
from Tools.LoadPixmap import LoadPixmap


class FileInfo(Screen, HelpableScreen):

	def __init__(self, session, filelist, fileindex):
		self.filelist = filelist
		self.fileindex = fileindex
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["FileInfo"]

		self["actions"] = HelpableActionMap(
			self,
			"MDCActions",
			{
				'ok':		(self.KeyExit,		_('Ok')),
				'right':	(self.KeyRight,		_('Next picture')),
				'left':		(self.KeyLeft,		_('Previous picture')),
				'exit':		(self.KeyExit,		_('Exit')),
				'red':		(self.KeyExit,		_('Exit')),
			},
			prio=-1
		)

		self.setTitle(_('Media Infos'))
		self['list'] = List()
		self['icon'] = Pixmap()
		self['pic'] = Pixmap()
		self['key_green'] = Button(_("Ok"))
		self['key_red'] = Button(_("Cancel"))
		self['key_yellow'] = Button()
		self['key_blue'] = Button()
		self.picload = ePicLoad()
		self.picload_conn = self.picload.PictureData.connect(self.decodePicture)
		self.onLayoutFinish.append(self.firstStart)

	def firstStart(self):
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara(
			[
				self['pic'].instance.size().width(),
				self['pic'].instance.size().height(),
				sc[0],
				sc[1],
				0,
				1,
				'#ff000000'
			]
		)
		self.fillList()

	def KeyLeft(self):
		self.fileindex -= 1
		if self.fileindex < 0:
			self.fileindex = len(self.filelist) - 1
		self.fillList()

	def KeyRight(self):
		self.fileindex += 1
		if self.fileindex > len(self.filelist) - 1:
			self.fileindex = 0
		self.fillList()

	def KeyExit(self):
		self.close(self.fileindex)

	def fillList(self):
		self.file = self.filelist[self.fileindex]
		self['pic'].hide()
		ptr = LoadPixmap(path=getSkinPath("images/" + self.file[FILE_TYPE] + '.svg'), cached=False)
		self['icon'].instance.setPixmap(ptr)
		self['icon'].show()
		alist = []
		alist.append((_('Filename'), self.file[FILE_PATH], None))
		date_time = datetime.fromtimestamp(self.file[FILE_DATE]).strftime('%Y:%m:%d %H:%M:%S')
		alist.append((_('Date'), date_time, None))
		metadata = {}
		if self.file[FILE_TYPE] == "picture":
			metadata = self.file[FILE_META]
			#print("MDC: FileInfo: fillList: metadata: %s" % str(metadata))
			tmpfile = rotatePictureExif(self.file[FILE_PATH], metadata)
			self.picload.startDecode(tmpfile)
			MeteringModeDesc = (
				_('unknown'),
				'Average',
				'Center-Weighted-Average',
				'Spot',
				'MultiSpot',
				'Pattern',
				'Partial')
			OrientDesc = (' ', 'Top-Left', 'Top-Right', 'Bottom-Right', 'Bottom-Left', 'Left-Top', 'Right-Top', 'Right-Bottom', 'Left-Bottom')
			ExposureProgram = (
				_('not defined'),
				'Manual',
				'Normal',
				'Aperture priority',
				'Shutter priority',
				'Creative',
				'Action',
				'Portrait',
				'Landscape')
			if 'Width' in metadata and 'Height' in metadata:
				alist.append((_('Width') + '/' + _('Height'), '%dx%d' % (metadata['Width'], metadata['Height']), None))
			if 'Model' in metadata:
				alist.append((_('Camera'), metadata['Model'], None))
			if 'Producer' in metadata:
				alist.append((_('Producer'), metadata['Producer'], None))
			if 'Date' in metadata:
				alist.append((_('Date') + '/' + _('Time'), metadata['Date'], None))
			if 'Flash' in metadata:
				alist.append((_('Flash'), str(metadata['Flash']), None))
			if 'Meteringmode' in metadata:
				alist.append((_('Metering-mode'), MeteringModeDesc[metadata['Meteringmode']], None))
			if 'ISO Speed Rating' in metadata:
				alist.append((_('ISO Speed Rating'), metadata['ISO Speed Rating'], None))
			if 'Orientation' in metadata:
				alist.append((_('Orientation'), OrientDesc[metadata['Orientation']], None))
			if 'Exposure-Program' in metadata:
				alist.append((_('Exposure-Program'), ExposureProgram[metadata['Exposure-Program']], None))
			if 'Software' in metadata:
				alist.append((_('Software'), metadata['Software'], None))
			if 'GPS-Altitude' in metadata:
				alist.append((_('Altitude'), metadata['GPS-Altitude'], None))
			if 'GPS-Latitude' in metadata and 'GPS-Longitude' in metadata:
				lat = metadata['GPS-Latitude']
				lng = metadata['GPS-Longitude']
				alist.append((_('Latitude'), lat, None))
				alist.append((_('Longitude'), lng, None))
		self['list'].setList(alist)
		self['list'].master.downstream_elements.setSelectionEnabled(0)

	def decodePicture(self, _picInfo=''):
		ptr = self.picload.getData()
		if ptr is not None:
			self['pic'].instance.setPixmap(ptr)
			self['pic'].show()
			self['icon'].hide()
