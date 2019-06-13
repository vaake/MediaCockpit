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
import time
from Components.config import config
from globals import FILE_PATH, FILE_DATE, FILE_FILTER
from globals import FILTER_GOUP, FILTER_DIR, FILTER_FILE, FILTER_LINK, FILTER_PLS
from PictureUtils import getExifData
from ConfigInit import sort_modes
from FileUtils import readFile

def sortList(filelist, sort_mode):

	mode, order = sort_modes[sort_mode][0]
	#print("MDC: FilelistUtils: sortList: sort_mode: %s, sort_order: %s" % (mode, order))

	if mode == "alpha":
		if order:
			filelist.sort(key=lambda x: (x[FILE_FILTER] & 0xF, x[FILE_PATH].lower()), reverse=True)
		else:
			filelist.sort(key=lambda x: (x[FILE_FILTER] & 0xF, x[FILE_PATH].lower()))
	elif mode == "date":
		if order:
			filelist.sort(key=lambda x: (x[FILE_FILTER] & 0xF, x[FILE_DATE]))
		else:
			filelist.sort(key=lambda x: (x[FILE_FILTER] & 0xF, x[FILE_DATE]), reverse=True)

	return filelist

def createGoupEntry(path, onlyfiles=False):
	#print("MDC: FileListUtils: createGoupEntry: path: %s" % path)
	goup = None
	if not onlyfiles and path != "/":
		goup = [os.path.dirname(path), FILTER_DIR + FILTER_GOUP, 0, 'goup', {}]
	return goup

def createFileEntry(path, filefilters, onlyfiles, onlydirs):
	#print("MDC: FileListUtils: createFileEntry: path: %s, filefilters: %s, onlyfiles: %s, onlydirs: %s" % (path, filefilters, onlyfiles, onlydirs))
	picture_exts = [".jpg", ".jpeg", ".png"]
	movie_exts = [".ts", ".m2ts", ".mp4"]
	playlist_exts = [".m3u"]
	music_exts = [".mp3"]

	x = None
	filetype = ""
	metadata = {}
	time_epoch = 0
	_filename, ext = os.path.splitext(path)
	ext = ext.lower()
	path_is_link = os.path.islink(path)
	if not (config.plugins.mediacockpit.skip_system_files.value and os.path.basename(path).startswith(".")):
		if not onlydirs and (os.path.isfile(path) or (path_is_link and ext)):
			filefilter = FILTER_FILE
			if "picture" in filefilters and ext in picture_exts:
				filetype = "picture"
				metadata = getExifData(path)
				if "DateTimeOriginal" in metadata:
					date_time = metadata["DateTimeOriginal"]
					try:
						time_tuple = time.strptime(date_time, '%Y:%m:%d %H:%M:%S')
						time_epoch = time.mktime(time_tuple)
					except ValueError:
						try:
							time_tuple = time.strptime(date_time, '%m:%d:%Y %H:%M')
							time_epoch = time.mktime(time_tuple)
						except ValueError as e:
							print("MCD-E: FileListUtils: createFileEntry: ValueError: %s" % e)
			elif "movie" in filefilters and ext in movie_exts:
				filetype = "movie"
			elif "playlist" in filefilters and ext in playlist_exts:
				filetype = "playlist"
				filefilter += FILTER_PLS
			elif "music" in filefilters and ext in music_exts:
				filetype = "music"
			ext = ext[1:]
		elif not onlyfiles and (os.path.isdir(path) or (path_is_link and not ext)):
			filefilter = FILTER_DIR
			filetype = "folder"
			ext = ""
		else:
			print("MDC-E: FileListUtils: scanDirectory: unsupported file type for path: %s" % path)

	if filetype:
		if path_is_link:
			path = os.path.realpath(path)
			filefilter += FILTER_LINK

		x = [path, filefilter, time_epoch, filetype, metadata]
	#print("MDC: FileListUtils: createFileEntry: x: %s" % str(x))
	return x


def scanDirectory(adir, filefilters=None, sort=None, skip_system_files=False, onlyfiles=False, onlydirs=False):
	#print("MDC: FileList: scanDirectory: adir: %s, filefilters: %s, sort: %s, skip_system_files: %s, onlyfiles: %s, onlydirs: %s" % (adir, str(filefilters), str(sort), skip_system_files, onlyfiles, onlydirs))

	filelist = []
	alist = []

	try:
		alist = os.listdir(adir)
	except OSError as e:
		print("MDC-E: FileListUtils: scanDirectory: listdir failed: e: %s" % e)

	for afile in alist:
		path = os.path.join(adir, afile)
		x = createFileEntry(path, filefilters, onlyfiles, onlydirs)
		if x is not None:
			filelist.append(x)
	if filelist:
		filelist = sortList(filelist, sort)
	return filelist

def processPlaylistEntry(filelist, path, sort):
	filefilters = ["picture", "movie"]
	if os.path.isfile(path):
		x = createFileEntry(path, filefilters, True, False)
		if x is not None:
			filelist.append(x)
	elif os.path.isdir(path):
		alist = scanDirectory(path, filefilters=["playlist"], sort=sort, skip_system_files=True, onlyfiles=True, onlydirs=False)
		alist += scanDirectory(path, filefilters=["picture", "movie"], sort=sort, skip_system_files=True, onlyfiles=True, onlydirs=False)
		filelist += alist
	return filelist


def scanPlaylist(path, sort):
	#print("MDC: PlayList: scanPlaylist: path: %s" % path)
	filelist = []
	playlist_dir = os.path.dirname(path)
	afile = readFile(path).splitlines()
	for line in afile:
		if line and not line.startswith("#"):
			#print("MDC: FileList: scanPlaylist: line: %s" % line)
			path = line
			adir = os.path.dirname(path)
			if not adir:
				path = os.path.join(playlist_dir, path)
			filelist = processPlaylistEntry(filelist, path, sort)
	#print("MDC: PlayList: scanPlaylist: filelist: %s" % str(filelist))
	return filelist
