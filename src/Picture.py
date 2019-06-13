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
from Movie import MDCMoviePlayer
from enigma import eTimer, getDesktop, gPixmapPtr
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Pixmap import MultiPixmap, Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import config
from PictureUtils import rotatePictureExif, rotatePicture
from ConfigScreen import ConfigScreen
from globals import FILE_FILTER, FILE_PATH, FILE_TYPE, FILE_META, FILTER_FILE, MDCTEMPFILE
from PixmapDisplay import PixmapDisplay
from FileUtils import deleteFile
from skin import colorNames
from SkinUtils import getSkinPath
from FileInfo import FileInfo


class MDCPictureSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		self.skinName = ['MDCSummary']


class MDCPicturePlayer(PixmapDisplay, Screen, HelpableScreen):

	def __init__(self, session, filelist, index, filelistsort=0):
		print("MDC-I: Picture: MDCPicturePlayer: __init__")
		self.slideshow_active = False
		self.filelistsort = filelistsort
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		#print("MDC: Picture: __init__: size_w: %s, size_h: %s" % (size_w, size_h))
		ico_mp_forward = getSkinPath('images/media-seek-forward.svg')
		ico_mp_rewind = getSkinPath('images/media-seek-backward.svg')
		self.skin =\
			'<screen position="0,0" size="1920,1080" flags="wfNoBorder" >\
				<widget name="BGlabel" position="0,0" zPosition="0" size="1920,1080" />\
				<widget name="pic" position="0,0" size="1920,1080" zPosition="1" />\
				<widget name="play_icon" position="5,3" size="25,25" zPosition="2" pixmaps="' + ico_mp_forward + ',' + ico_mp_rewind + '" alphatest="on" />\
				<widget name="label" position="35,5" size="1885,25" font="Regular;18" halign="left" zPosition="2" noWrap="1" transparent="1" />\
			</screen>'
		PixmapDisplay.__init__(self)
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["actions"] = HelpableActionMap(
			self,
			"MDCActions",
			{
				'menu':		(self.KeyMenu,		_('Settings')),
				'info':		(self.KeyInfo,		_('Information')),
				'playpause':	(self.PlayPause,	_('Pause / Resume') + ' ' + _('Slideshow')),
				'stop':		(self.stopSlideshow,	_('Stop') + ' ' + _('Slideshow')),
				'historyNext':	(self.nextFile,		_('Next picture')),
				'right':	(self.nextFile,		_('Next picture')),
				'historyBack':	(self.prevFile,		_('Previous picture')),
				'left':		(self.prevFile,		_('Previous picture')),
				'yellow':	(self.rotateFile,	_('Rotate picture')),
				'blue':		(self.toggleInfo,	_('Toggle info')),
				'exit':		(self.KeyExit,		_('Exit')),
				'red':		(self.KeyExit,		_('Exit')),
			},
			prio=-1
		)

		self['BGlabel'] = Label()
		self['pic'] = Pixmap()
		self['play_icon'] = MultiPixmap()
		self['label'] = Label()
		self['lcdinfo'] = StaticText()
		self['title'] = StaticText()

		self.filelist = filelist
		self.fileindex = index

		self.tempfile = None
		self.direction = 1
		self.slideTimer = eTimer()
		self.slideTimer_conn = self.slideTimer.timeout.connect(self.nextSlide)
		self.onLayoutFinish.append(self.LayoutFinish)

	def createSummary(self):
		return MDCPictureSummary

	def KeyExit(self):
		deleteFile(os.path.join(config.plugins.mediacockpit.cache_dir.value, MDCTEMPFILE) + ".*")
		config.plugins.mediacockpit.save()
		self.close(self.fileindex)

	def LayoutFinish(self):
		#print("MDC: Picture: LayoutFinish")
		self.bgcolor = colorNames[config.plugins.mediacockpit.picture_background.value]
		self.fgcolor = colorNames[config.plugins.mediacockpit.picture_foreground.value]
		self.showInfoLine = config.plugins.mediacockpit.infobar.value
		self.slidetimer = config.plugins.mediacockpit.slidetimer.value * 1000
		self['pic'].instance.setShowHideAnimation(config.plugins.mediacockpit.animation.value)
		self['label'].instance.setShowHideAnimation(config.plugins.mediacockpit.animation.value)
		self['BGlabel'].instance.setBackgroundColor(self.bgcolor)
		self['label'].instance.setForegroundColor(self.fgcolor)
		self['label'].instance.setBackgroundColor(self.bgcolor)
		self['BGlabel'].instance.invalidate()
		self.showFile()

	def updateInfo(self):
		if self.showInfoLine:
			self['play_icon'].setPixmapNum(0 if self.direction > 0 else 1)
			self['label'].setText('(%d/%d) %s' % (self.fileindex + 1, len(self.filelist), self.filelist[self.fileindex][FILE_PATH]))
			self['label'].show()

			if self.slideshow_active:
				self['play_icon'].show()
			else:
				self['play_icon'].hide()
		else:
			self['play_icon'].hide()
			self['label'].hide()

	def nextSlide(self):
		#print("MDC: Picture: nextSlide")
		if self.direction > 0:
			self.nextFile()
		elif self.direction < 0:
			self.prevFile()

	def showFile(self):
		self.file = self.filelist[self.fileindex]
		print("MDC-I: Picture: showFile: index: %s, file: %s" % (self.fileindex, str(self.file)))
		self.updateInfo()
		if self.file[FILE_TYPE] == 'picture':
			self.showPicture(self.file[FILE_PATH])
		elif self.file[FILE_TYPE] == 'movie':
			self.showMovie()
		else:
			self.nextSlide()

	def showMovie(self):
		#print("MDC: Picture: showMovie: index: %s, file: %s" % (self.fileindex, str(self.file)))
		if self.slideTimer.isActive():
			self.slideTimer.stop()
		empty = gPixmapPtr()
		self['pic'].instance.setPixmap(empty)
		self.session.openWithCallback(self.showMovieCallback, MDCMoviePlayer, [self.file], 0, leave_quietly=True, resume=False)

	def showMovieCallback(self, _val=None, _val1=None, _val2=None):
		#print("MDC: Picture: showMovieCallback: movie playback done, val: %s" % _val)
		if self.slideshow_active:
			self.slideTimer.start(self.slidetimer)
		self.nextSlide()

	def showPicture(self, path):
		#print("MDC: Picture: showPicture: show picture: path: %s, index: %s" % (path, self.fileindex))
		if self.showInfoLine:
			self['label'].setText('(%d/%d) %s' % (self.fileindex + 1, len(self.filelist), os.path.basename(path)))
		self['title'].setText('%d/%d' % (self.fileindex + 1, len(self.filelist)))
		self['lcdinfo'].setText(os.path.basename(path))
		if config.plugins.mediacockpit.rotate.value:
			metadata = self.filelist[self.fileindex][FILE_META]
			path = rotatePictureExif(path, metadata)
		self.displayPixmap(self["pic"], path)

	def toggleInfo(self):
		self.showInfoLine = not self.showInfoLine
		self.updateInfo()

	def rotateFile(self):
		if self.filelist[self.fileindex][FILE_TYPE] == "picture":
			if self.tempfile is None:
				src_file = self.filelist[self.fileindex][FILE_PATH]
			else:
				src_file = self.tempfile
			self.tempfile = rotatePicture(src_file, -90)
			self.displayPixmap(self["pic"], self.tempfile)

	def nextFile(self):
		self.direction = 1
		self.fileindex += 1
		if self.fileindex > len(self.filelist) - 1:
			self.fileindex = 0
		#print("MDC: Picture: next: self.fileindex: %s" % self.fileindex)
		self.file = self.filelist[self.fileindex]
		self.showFile()

	def prevFile(self):
		self.direction = -1
		self.fileindex -= 1
		if self.fileindex < 0:
			self.fileindex = len(self.filelist) - 1
		#print("MDC: Picture: prev: self.fileindex: %s" % self.fileindex)
		self.file = self.filelist[self.fileindex]
		self.showFile()

	def startSlideshow(self):
		self.slideshow_active = True
		self.slideTimer.start(self.slidetimer)
		self.updateInfo()

	def stopSlideshow(self):
		self.slideshow_active = False
		if self.slideTimer.isActive():
			self.slideTimer.stop()
		self.updateInfo()

	def PlayPause(self):
		if self.slideshow_active:
			self.stopSlideshow()
		else:
			self.startSlideshow()
			self.nextSlide()

	def KeyInfo(self):
		if not self.slideshow_active:
			if self.filelist[self.fileindex][FILE_FILTER] == FILTER_FILE:
				self.session.openWithCallback(self.KeyInfoCallback, FileInfo, self.filelist, self.fileindex)

	def KeyInfoCallback(self, index):
		self.fileindex = index
		self.LayoutFinish()

	def KeyMenu(self):
		if not self.slideshow_active:
			self.session.openWithCallback(self.KeyMenuCallback, ConfigScreen, "picture")

	def KeyMenuCallback(self, _reload):
		self.LayoutFinish()
