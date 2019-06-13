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
from skin import colorNames
from enigma import eWindowAnimationManager
from Components.config import config, ConfigInteger, ConfigText, ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave, ConfigLocations


choices_launch_key = [
	("None",		_("No override")),
	("showMovies",		_("Video-button")),
	("showTv",		_("TV-button")),
	("showRadio",		_("Radio-button")),
	("openQuickbutton",	_("Quick-button")),
	("startTimeshift",	_("Timeshift-button"))
]


choices_date = [
	("%d.%m.%Y",		_("DD.MM.YYYY")),
	("%a %d.%m.%Y",		_("WD DD.MM.YYYY")),

	("%d.%m.%Y %H:%M",	_("DD.MM.YYYY HH:MM")),
	("%a %d.%m.%Y %H:%M",	_("WD DD.MM.YYYY HH:MM")),

	("%d.%m. %H:%M",	_("DD.MM. HH:MM")),
	("%a %d.%m. %H:%M",	_("WD DD.MM. HH:MM")),

	("%Y/%m/%d",		_("YYYY/MM/DD")),
	("%a %Y/%m/%d",		_("WD YYYY/MM/DD")),

	("%Y/%m/%d %H:%M",	_("YYYY/MM/DD HH:MM")),
	("%a %Y/%m/%d %H:%M",	_("WD YYYY/MM/DD HH:MM")),

	("%m/%d %H:%M",		_("MM/DD HH:MM")),
	("%a %m/%d %H:%M",	_("WD MM/DD HH:MM"))
]


sort_modes = {
	"0": (("date", False),	_("Date sort down")),
	"1": (("date", True), 	_("Date sort up")),
	"2": (("alpha", False),	_("Alpha sort up")),
	"3": (("alpha", True),	_("Alpha sort down"))
}


choices_sort = [(k, v[1]) for k, v in sort_modes.items()]


choices_cache = [
	('/root/.cache/mdc', 'root'),
	('/home/.cache/mdc', 'home'),
	('/data/.cache/mdc', 'data'),
	('/media/hdd/.cache/mdc', 'hdd'),
]


choices_color = []
for key in colorNames.iterkeys():
	choices_color.append((key, _(key)))


animations = eWindowAnimationManager.getAnimations()
choices_animation = []
for key, name in animations.iteritems():
	choices_animation.append((key, name))


class ConfigInit(object):

	def __init__(self):
		#print("MDC: ConfigInit: __init__")
		config.plugins.mediacockpit                            = ConfigSubsection()
		config.plugins.mediacockpit.stop_tv_playback           = ConfigYesNo(default=True)
		config.plugins.mediacockpit.sort                       = ConfigSelection(default="2", choices=choices_sort)
		config.plugins.mediacockpit.skip_system_files          = ConfigYesNo(default=True)
		config.plugins.mediacockpit.cache_dir                  = ConfigSelection(default='/data/.cache/mdc', choices=choices_cache)
		config.plugins.mediacockpit.last_path                  = ConfigText(default='/media')
		config.plugins.mediacockpit.start_home_dir             = ConfigYesNo(default=False)
		config.plugins.mediacockpit.home_dir                   = ConfigText(default='/media', fixed_size=False, visible_width=35)
		config.plugins.mediacockpit.frame                      = ConfigYesNo(default=True)
		config.plugins.mediacockpit.selection_size_offset      = ConfigInteger(default=10, limits=(0, 50))
		config.plugins.mediacockpit.selection_font_offset      = ConfigInteger(default=2, limits=(1, 10))
		config.plugins.mediacockpit.normal_background_color    = ConfigSelection(default="#20294071", choices=choices_color + [("#20294071", _("default"))])
		config.plugins.mediacockpit.selection_background_color = ConfigSelection(default="#204176b6", choices=choices_color + [("#204176b6", _("default"))])
		config.plugins.mediacockpit.normal_foreground_color    = ConfigSelection(default="#eeeeee", choices=choices_color + [("#eeeeee", _("default"))])
		config.plugins.mediacockpit.selection_foreground_color = ConfigSelection(default="#ffffff", choices=choices_color + [("#ffffff", _("default"))])
		config.plugins.mediacockpit.selection_frame_color      = ConfigSelection(default="#b3b3b9", choices=choices_color + [("#b3b3b9", _("default"))])
		config.plugins.mediacockpit.slidetimer                 = ConfigInteger(default=5, limits=(3, 30))
		config.plugins.mediacockpit.animation                  = ConfigSelection(default='simple_fade', choices=choices_animation)
		config.plugins.mediacockpit.picture_background         = ConfigSelection(default='background', choices=choices_color)
		config.plugins.mediacockpit.picture_foreground         = ConfigSelection(default='foreground', choices=choices_color)
		config.plugins.mediacockpit.rotate                     = ConfigYesNo(default=True)
		config.plugins.mediacockpit.infobar                    = ConfigYesNo(default=True)
		config.plugins.mediacockpit.launch_key                 = ConfigSelection(default="None", choices=choices_launch_key)
		config.plugins.mediacockpit.mediadirs                  = ConfigLocations(default=["/media"])
		config.plugins.mediacockpit.fake_entry                 = NoSave(ConfigNothing())
		config.plugins.mediacockpit.debug                      = ConfigYesNo(default=False)
		config.plugins.mediacockpit.debug_log_path             = ConfigText(default="/media/hdd", fixed_size=False, visible_width=35)
