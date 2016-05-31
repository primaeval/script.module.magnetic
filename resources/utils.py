# -*- coding: utf-8 -*-

import os
import re
from json import loads
from urllib2 import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
PATH_ADDONS = xbmc.translatePath("special://home/addons/")
# provider service config
PROVIDER_SERVICE_HOST = "localhost"
PROVIDER_SERVICE_PORT = 5005


def check_provider(provider=""):
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    url = magnetic_url + "?search=general&title=spectre&provider=%s" % provider
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except:
        pass
    return results.get('duration', 'error')


def get_list_providers():
    results = []
    list_providers = loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                               '"method": "Addons.GetAddons", '
                                               '"id": 1, '
                                               '"params": {"type" : "xbmc.python.script", '
                                               '"properties": ["enabled", "name", "fanart"]}}'))
    for provider1 in list_providers["result"]["addons"]:
        if not provider1['addonid'].startswith('script.magnetic.'):
            continue
        results.append(provider1)
    return results


def disable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":false}}' % provider)


def enable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":true}}' % provider)


def disable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":false}}' % provider)


def enable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":true}}' % provider)


# Borrowed from xbmcswift2
def get_setting(key, converter=str, choices=None):
    value = ADDON.getSetting(id=key)
    if converter is str:
        return value
    elif converter is unicode:
        return value.decode('utf-8')
    elif converter is bool:
        return value == 'true'
    elif converter is int:
        return int(value)
    elif isinstance(choices, (list, tuple)):
        return choices[int(value)]
    else:
        raise TypeError('Acceptable converters are str, unicode, bool and '
                        'int. Acceptable choices are instances of list '
                        ' or tuple.')


def get_icon_path():
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'icon.png')


class Magnet:
    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(.*?)&', self.magnet)
        result = ''
        if info_hash is not None:
            result = info_hash.group(1)
        self.info_hash = result
        # name
        name = re.search('dn=(.*?)&', self.magnet)
        result = ''
        if name is not None:
            result = name.group(1).replace('+', ' ')
        self.name = result.title()
        # trackers
        self.trackers = re.findall('tr=(.*?)&', self.magnet)


def get_int(text):
    # noinspection PyBroadException
    try:
        value = int(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


# noinspection PyBroadException
def size_int(size_txt):
    try:
        return int(size_txt)
    except:
        size_txt = size_txt.upper()
        size1 = size_txt.replace('B', '').replace('I', '').replace('K', '').replace('M', '').replace('G', '')
        size = get_float(size1)
        if 'K' in size_txt:
            size *= 1000
        if 'M' in size_txt:
            size *= 1000000
        if 'G' in size_txt:
            size *= 1e9
        return get_int(size)


def get_float(text):
    # noinspection PyBroadException
    try:
        value = float(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


def notify(message, image=None):
    dialog = xbmcgui.Dialog()
    dialog.notification(ADDON_NAME, message, icon=image)
    del dialog
