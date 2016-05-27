import json
import sys
from os import path
from re import findall
from urlparse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = dict(parse_qsl(sys.argv[2][1:]))


def get_list_providers():
    results = []
    list_providers = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                                    '"method": "Addons.GetAddons", '
                                                    '"id": 1, '
                                                    '"params": {"type" : "xbmc.python.script", '
                                                    '"properties": ["enabled", "name", "fanart"]}}'))
    for provider in list_providers["result"]["addons"]:
        if not provider['addonid'].startswith('script.magnetic.'):
            continue
        results.append(provider)
    return results


listing = []

mode = args.get('mode', '')
addonid = args.get('addonid', '')

if 'provider' in mode:
    xbmcaddon.Addon(addonid).openSettings()

elif 'settings' in mode:
    xbmcaddon.Addon().openSettings()

elif 'copy' in mode:
    path_folder = xbmcaddon.Addon(addonid).getAddonInfo('path')
    value = dict()  # it contains all the settings from xml file
    fileName = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(fileName):
        with open(fileName, 'r') as fp:
            data = fp.read()
        for key in findall('id="(\w+)"', data):
            if 'url' not in key and 'separator' not in key:
                value[key] = xbmcaddon.Addon(addonid).getSetting(id=key)

        items = ['All providers'] + [provider['addonid'] for provider in get_list_providers()]
        items.remove(addonid)
        ret = xbmcgui.Dialog().select('Select the provider', items)
        if ret != -1:
            del items[0]
            for key, val in value.items():
                for provider in (items if ret > 0 else [items[ret - 1]]):
                    xbmcaddon.Addon(provider).setSetting(id=key, value=val)
        xbmcgui.Dialog().notification('Magnetic', 'All the settings were copied')

elif 'enable' in mode:
    xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid":"%s","enabled":true}}' % addonid)
    mode = ''
    xbmc.executebuiltin("Container.Refresh")

elif 'disable' in mode:
    xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid":"%s","enabled":false}}' % addonid)
    mode = ''
    xbmc.executebuiltin("Container.Refresh")

if len(mode) == 0:
    # creation menu
    for provider in get_list_providers():
        name_provider = provider['name']  # gets name
        tag = "[ENABLE] "
        menu_item = (
            'Disable', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable&addonid=%s)' % provider['addonid'])
        if not provider['enabled']:
            tag = "[DISABLE] "
            menu_item = (
                'Enable',
                'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable&addonid=%s)' % provider['addonid'])
        list_item = xbmcgui.ListItem(label=tag + name_provider)
        icon = provider["fanart"]
        fanart = provider["fanart"]
        list_item.setArt({'thumb': icon,
                          'icon': icon,
                          'fanart': fanart})
        url = base_url + '?mode=provider&addonid=%s' % provider['addonid']
        is_folder = False
        list_item.addContextMenuItems([('Check', 'Container.Refresh'),
                                       ('Check All', 'Container.Refresh'),
                                       menu_item,
                                       ('Copy Settings To...',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=copy&addonid=%s)' %
                                        provider['addonid']),
                                       ('Add-on Settings',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=settings)')],
                                      replaceItems=True)
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(addon_handle, listing, len(listing))
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addon_handle)
