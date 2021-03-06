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
ADDON_ICON = ADDON.getAddonInfo("icon")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_VERSION = ADDON.getAddonInfo("version")
PATH_ADDONS = xbmc.translatePath("special://home/addons/")
PATH_TEMP = xbmc.translatePath("special://temp")
# provider service config
PROVIDER_SERVICE_HOST = "127.0.0.1"
PROVIDER_SERVICE_PORT = 5005


# noinspection PyBroadException
def check_provider(provider=""):
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    title = 'simpsons'
    if 'nyaa' in provider:
        title = 'one%20piece'
    if 'yts' in provider:
        title = 'batman%201989'
    url = magnetic_url + "?search=general&title=%s&provider=%s" % (title, provider)
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except:
        pass
    duration = results.get('duration', '[COLOR FFC40401]Error[/COLOR]')
    items = results.get('results', 'zero')
    return " [%s for %s items]" % (duration, items)


# noinspection PyBroadException
def check_group_provider():
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    title = '12%20monkeys'
    url = magnetic_url + "?search=general&title=%s" % title
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except:
        pass
    duration = results.get('duration', '[COLOR FFC40401]Error[/COLOR]')
    items = results.get('results', 'zero')
    return " [%s for %s items]" % (duration, items)


def get_list_providers():
    results = []
    list_providers = loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                               '"method": "Addons.GetAddons", '
                                               '"id": 1, '
                                               '"params": {"type" : "xbmc.python.script", '
                                               '"properties": ["enabled", "name", "thumbnail", "fanart"]}}'))
    for one_provider in list_providers["result"]["addons"]:
        if one_provider['addonid'].startswith('script.magnetic.'):
            results.append(one_provider)
    return results


def get_list_providers_enabled():
    results = []
    list_providers = loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                               '"method": "Addons.GetAddons", '
                                               '"id": 1, '
                                               '"params": {"type" : "xbmc.python.script", '
                                               '"properties": ["enabled", "name"]}}'))
    for one_provider in list_providers["result"]["addons"]:
        if one_provider['addonid'].startswith('script.magnetic.') and one_provider['enabled']:
            results.append(one_provider['addonid'])
    return results


def disable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":false}}' % provider)


def enable_provider(provider):
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":true}}' % provider)


# Borrowed from xbmc swift2
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


def string(id_value):
    return xbmcaddon.Addon().getLocalizedString(id_value)


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
    return int(get_float(text))


def get_float(text):
    value = 0
    if isinstance(text, (float, long, int)):
        value = float(text)
    elif isinstance(text, str):
        # noinspection PyBroadException
        try:
            text = clean_number(text)
            match = re.search('([0-9]*\.[0-9]+|[0-9]+)', text)
            if match:
                value = float(match.group(0))
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
        return size


def clean_number(text):
    comma = text.find(',')
    point = text.find('.')
    if comma > 0 and point > 0:
        if comma < point:
            text = text.replace(',', '')
        else:
            text = text.replace('.', '')
            text = text.replace(',', '.')
    return text


def notify(message, image=None):
    dialog = xbmcgui.Dialog()
    dialog.notification(ADDON_NAME, message, icon=image)
    del dialog


def display_message_cache():
    p_dialog = xbmcgui.DialogProgressBG()
    p_dialog.create('Magnetic Manager', string(32061))
    xbmc.sleep(250)
    p_dialog.update(25, string(32065))
    xbmc.sleep(250)
    p_dialog.update(50, string(32065))
    xbmc.sleep(250)
    p_dialog.update(75, string(32065))
    xbmc.sleep(250)
    p_dialog.close()
    del p_dialog
