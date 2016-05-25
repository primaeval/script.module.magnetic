import sys
import json
from urlparse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = dict(parse_qsl(sys.argv[2][1:]))

listing = []

mode = args.get('mode', '')
name = args.get('name', '')

if 'provider' in mode:
    xbmcaddon.Addon(name).openSettings()
elif 'settings' in mode:
    xbmcaddon.Addon().openSettings()
elif 'enable' in mode:
    xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid":"%s","enabled":true}}' % name)
    mode = ''
    xbmc.executebuiltin("Container.Refresh")
elif 'disable' in mode:
    xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid":"%s","enabled":false}}' % name)
    mode = ''
    xbmc.executebuiltin("Container.Refresh")
if len(mode) == 0:
    # creation menu
    list_providers = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                                    '"method": "Addons.GetAddons", '
                                                    '"id": 1, '
                                                    '"params": {"type" : "xbmc.python.script", '
                                                    '"properties": ["enabled", "name", "fanart"]}}'))
    for provider in list_providers["result"]["addons"]:
        if not provider['addonid'].startswith('script.magnetic.'):
            continue
        print "HERE HERE HERE"
        name_provider = provider['name']  # gets name
        tag = "[ENABLE] "
        menu_item = (
            'Disable', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable&name=%s)' % provider['addonid'])
        if not provider['enabled']:
            tag = "[DISABLE] "
            menu_item = (
                'Enable', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable&name=%s)' % provider['addonid'])
        list_item = xbmcgui.ListItem(label=tag + name_provider)
        icon = provider["fanart"]
        fanart = provider["fanart"]
        list_item.setArt({'thumb': icon,
                          'icon': icon,
                          'fanart': fanart})
        url = base_url + '?mode=provider&name=%s' % provider['addonid']
        is_folder = False
        list_item.addContextMenuItems([('Check', 'Container.Refresh'),
                                       ('Check All', 'Container.Refresh'),
                                       menu_item,
                                       ('Add-on Settings',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=settings)')],
                                      replaceItems=True)
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(addon_handle, listing, len(listing))
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addon_handle)
