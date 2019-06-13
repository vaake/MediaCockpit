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

from Tools.Directories import fileExists, resolveFilename, SCOPE_SKIN, SCOPE_CURRENT_SKIN


def getSkinPath(filename):
	#print("MDC: SkinUtils: getSkinPath: filename: %s" % filename)
	skin_path = resolveFilename(SCOPE_CURRENT_SKIN, "MediaCockpit/skin/" + filename)
	if not fileExists(skin_path):
		skin_path = resolveFilename(SCOPE_SKIN, "Default-FHD/MediaCockpit/skin/" + filename)
	#print("MDC: SkinUtils: getSkinPath: skin_path: " + skin_path)
	return skin_path
