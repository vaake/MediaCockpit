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
from globals import MDCTEMPFILE
from PIL import Image
from enigma import eRect
from PIL.ExifTags import TAGS
from Components.config import config


def getExifData(path):
	#print("MDC: PictureUtils: getExifData: path: %s" % path)
	exif_data = None
	try:
		img = Image.open(path)
		if img and hasattr(img, "_getexif"):
			exif_data = img._getexif()
	except Exception as e:
		print("MDC-E: PictureUtils: getExifData: PIL error: %s" % e)
	exif = {}
	if exif_data is not None:
		for key, value in exif_data.iteritems():
			if key in TAGS:
				tag = TAGS[key]
				if tag != "UserComment" and tag != "MakerNote":
					exif[tag] = value
	#print("MDC: PictureUtils: getExifData: exif: %s" % str(exif))
	return exif


def rotatePicture(path, degrees):
	_filename, ext = os.path.splitext(path)
	tmpfile = os.path.join(config.plugins.mediacockpit.cache_dir.value, MDCTEMPFILE) + ext
	img = Image.open(path)
	tmpimg = img.rotate(degrees, resample=Image.NEAREST)
	tmpimg.save(tmpfile)
	return tmpfile


def rotatePictureExif(path, exif_infos):
	#print("MDC: PictureUtils: rotatePictureExif: path: %s, exif_infos: %s" % (path, str(exif_infos)))
	orientation = 1
	tmpfile = path
	_filename, ext = os.path.splitext(path)
	if "Orientation" in exif_infos:
		orientation = exif_infos["Orientation"]
		if orientation != 1 and ext != ".svg":
			#print("MDC: PictureUtils: rotatePictureExif: pic needs to be rotated")
			tmpfile = os.path.join(config.plugins.mediacockpit.cache_dir.value, MDCTEMPFILE) + ext
			img = Image.open(path)
			if img:
				if orientation == 8:
					tmpimg = img.rotate(90, resample=Image.NEAREST)
					tmpimg.save(tmpfile)
				if orientation == 6:
					tmpimg = img.rotate(-90, resample=Image.NEAREST)
					tmpimg.save(tmpfile)
				if orientation == 3:
					tmpimg = img.rotate(-180, resample=Image.NEAREST)
					tmpimg.save(tmpfile)
	#print("MDC: PictureUtils: rotatePictureExif: tmpfile: %s" % tmpfile)
	return tmpfile


def setFullPixmap(dest, ptr, scaleSize, aspectRatio):
	if scaleSize.isValid() and aspectRatio.isValid():
		pic_scale_size = ptr.size().scale(scaleSize, aspectRatio)
		dest_size = dest.getSize()
		dest_width = dest_size.width()
		dest_height = dest_size.height()
		pic_scale_width = pic_scale_size.width()
		pic_scale_height = pic_scale_size.height()
		if pic_scale_width == dest_width:
			dest_rect = eRect(0, (dest_height - pic_scale_height) / 2, pic_scale_width, pic_scale_height)
		else:
			dest_rect = eRect((dest_width - pic_scale_width) / 2, 0, pic_scale_width, pic_scale_height)
		dest.instance.setScale(1)
		dest.instance.setScaleDest(dest_rect)
	else:
		dest.instance.setScale(0)
	dest.instance.setPixmap(ptr)


def setThumbPixmap(dest, ptr):
	pic_size = ptr.size()
	pic_width = pic_size.width()
	pic_height = pic_size.height()
	dest_size = dest.getSize()
	dest_width = dest_size.width()
	dest_height = dest_size.height()
	if pic_width == dest_width:
		dest_rect = eRect(0, (dest_height - pic_height) / 2, pic_width, pic_height)
	else:
		dest_rect = eRect((dest_width - pic_width) / 2, 0, pic_width, pic_height)
	dest.instance.setScale(1)
	dest.instance.setScaleDest(dest_rect)
	dest.instance.setPixmap(ptr)
