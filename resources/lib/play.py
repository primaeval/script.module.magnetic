# -*- coding: utf-8 -*-
from json import loads
from urllib2 import Request, urlopen

import xbmcgui

from dialog_select import DialogSelect
from provider import *
from utils import string

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo("path")


def play(magnet):
    plugin = get_setting('plugin')
    uri_string = get_playable_link(magnet)
    if plugin == 'Quasar':
        link = 'plugin://plugin.video.quasar/play?uri=%s' % uri_string
    elif plugin == 'Pulsar':
        link = 'plugin://plugin.video.pulsar/play?uri=%s' % uri_string
    elif plugin == 'KmediaTorrent':
        link = 'plugin://plugin.video.kmediatorrent/play/%s' % uri_string
    elif plugin == "Torrenter":
        link = 'plugin://plugin.video.torrenter/?action=playSTRM&url=' + uri_string + \
               '&not_download_only=True'
    elif plugin == "YATP":
        link = 'plugin://plugin.video.yatp/?action=play&torrent=' + uri_string
    else:
        link = 'plugin://plugin.video.xbmctorrent/play/%s' % uri_string
    # play media
    xbmc.executebuiltin("PlayMedia(%s)" % link)
    xbmc.executebuiltin('Dialog.Close(all, true)')


# noinspection PyBroadException,PyTypeChecker
def search(query=""):
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    url = magnetic_url + "?search=general&title=%s" % query.replace(' ', '%20')
    log.debug(url)
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except:
        pass
    items = results.get('magnets', None)
    if items is None or len(items) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok("Magnetic", string(32075))
        del dialog
    else:
        window = DialogSelect("DialogSelectLarge.xml", ADDON_PATH, "Default", title=string(32074) % query,
                              items=items)
        window.doModal()
        selection = window.ret
        del window
        if selection > -1:
            play(items[selection]['uri'])
