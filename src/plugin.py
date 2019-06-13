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


import os
from __init__ import _
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from Components.config import config
from enigma import getDesktop
from skin import loadSkin, loadSingleSkinData, dom_skins
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS
from SkinUtils import getSkinPath
from Tools.BoundFunction import boundFunction
from Version import VERSION
from Cockpit import Cockpit
from ConfigInit import ConfigInit
from FileUtils import createDirectory


def loadPluginSkin(skin_file):
	default_skin = resolveFilename(SCOPE_SKIN, "Default-FHD/MediaCockpit")
	current_skin = resolveFilename(SCOPE_CURRENT_SKIN, "MediaCockpit")
	plugin_skin = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaCockpit")
	print("MDC-I: plugin: loadPluginSkin: current_skin: %s" % current_skin)
	print("MDC-I: plugin: loadPluginSkin: default_skin: %s" % default_skin)
	print("MDC-I: plugin: loadPluginSkin: plugin_skin: %s" % plugin_skin)
	if not (os.path.islink(default_skin) or os.path.isdir(default_skin)):
		print("MDC-I: plugin: loadPluginSkin: ln -s " + plugin_skin + " " + resolveFilename(SCOPE_SKIN, "Default-FHD"))
		os.system("ln -s " + plugin_skin + " " + resolveFilename(SCOPE_SKIN, "Default-FHD"))
	loadSkin(getSkinPath(skin_file), "")
	path, dom_skin = dom_skins[-1:][0]
	loadSingleSkinData(getDesktop(0), dom_skin, path)


def autoStart(reason, **kwargs):
	print("MDC-I: plugin: autoStart: reason: %s" % reason)
	if reason == 0:  # startup
		if "session" in kwargs:
			print("MDC-I: plugin: autoStart: +++ Version: " + VERSION + " starts...")
			session = kwargs["session"]
			ConfigInit()
			print("MDC-I: plugin: autoStart: cache_dir: %s" % config.plugins.mediacockpit.cache_dir.value)
			createDirectory(config.plugins.mediacockpit.cache_dir.value)

			launch_key = config.plugins.mediacockpit.launch_key.value
			if launch_key == "showMovies":
				InfoBar.showMovies = boundFunction(startMediaCockpit, session)
			elif launch_key == "showTv":
				InfoBar.showTv = boundFunction(startMediaCockpit, session)
			elif launch_key == "showRadio":
				InfoBar.showRadio = boundFunction(startMediaCockpit, session)
			elif launch_key == "openQuickbutton":
				InfoBar.openQuickbutton = boundFunction(startMediaCockpit, session)
			elif launch_key == "startTimeshift":
				InfoBar.startTimeshift = boundFunction(startMediaCockpit, session)
	elif reason == 1:  # shutdown
		print("MDC-I: plugin: autoStart: --- shutdown")
	else:
		print("MDC-I: plugin: autoStart: reason not handled: %s" % reason)


def startMediaCockpit(session, **__):
	loadPluginSkin("skin.xml")
	session.open(Cockpit)


def Plugins(**__):
	return [
		PluginDescriptor(
			name=_('MediaCockpit'),
			description=_('Pictures, Movies, and Slideshows'),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=startMediaCockpit,
			icon='skin/images/icon_mediacockpit.svg'
		),
		PluginDescriptor(
			where=[
				PluginDescriptor.WHERE_SESSIONSTART,
				PluginDescriptor.WHERE_AUTOSTART
			],
			fnc=autoStart,
		),
	]
