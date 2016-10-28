import sys
from os import path
from re import findall
from urlparse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import resources.storage
import resources.utils as utils

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = dict(parse_qsl(sys.argv[2][1:]))

listing = []
storage_info = resources.storage.Storage(xbmc.translatePath('special://profile/addon_data/script.module.magnetic/'))
speed_providers = storage_info["speed"]

mode = args.get('mode', '')
addonid = args.get('addonid', '')


def erase():
    database = storage_info["providers"]
    database.clear()
    xbmcgui.Dialog().ok('Magnetic', 'Cache Cleared!')


if mode == 'provider':
    xbmcaddon.Addon(addonid).openSettings()

elif mode == 'settings':
    xbmcaddon.Addon().openSettings()

elif mode == 'clear_cache':
    erase()

elif mode == 'copy':
    path_folder = xbmcaddon.Addon(addonid).getAddonInfo('path')
    value = dict()  # it contains all the settings from xml file
    fileName = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(fileName):
        with open(fileName, 'r') as fp:
            data = fp.read()
        for key in findall('id="(\w+)"', data):
            if 'url' not in key and 'separator' not in key:
                value[key] = xbmcaddon.Addon(addonid).getSetting(id=key)

        items = []
        for provider in utils.get_list_providers():
            if provider['enabled']:
                items.append(provider['addonid'])
        items.remove(addonid)
        ret = xbmcgui.Dialog().select('Select the provider', ['All providers'] + items + ['CANCEL'])
        list_copy = (items if ret == 0 else [items[ret - 1]])
        if ret != -1 and ret <= len(items):
            for key, val in value.items():
                if not key.endswith('_search') and 'read_magnet_link' not in key:
                    for provider in list_copy:
                        xbmcaddon.Addon(provider).setSetting(id=key, value=val)
            xbmcgui.Dialog().ok('Magnetic', 'The %s settings were copied to \n%s' % (addonid, '\n'.join(list_copy)))


elif mode == 'check':
    speed_providers[addonid] = utils.check_provider(addonid)
    speed_providers.sync()
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'check_all':
    from xbmcgui import Dialog

    dialog = Dialog()
    for provider in utils.get_list_providers():
        if provider['enabled']:
            dialog.notification(provider['name'],
                                "Checking speed",
                                provider['thumbnail'], 10000)
            speed_providers[provider['addonid']] = utils.check_provider(provider['addonid'])
            speed_providers.sync()
    dialog.notification('Magnetic', 'Done!', time=50)
    del dialog
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'enable':
    utils.enable_provider(addonid)
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'disable':
    utils.disable_provider(addonid)
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'enable_all':
    for provider in utils.get_list_providers():
        utils.enable_provider(provider['addonid'])
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'disable_all':
    for provider in utils.get_list_providers():
        utils.disable_provider(provider['addonid'])
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'defaults_all':
    import shutil
    import os.path

    base_path = xbmc.translatePath('special://userdata/addon_data')
    for provider in utils.get_list_providers():
        folder = path.join(base_path, provider['addonid'])
        if os.path.isfile(folder):
            shutil.rmtree(folder)
    xbmcgui.Dialog().ok('Magnetic', 'Defaults settings applied')

if len(mode) == 0:
    # creation menu
    for provider in utils.get_list_providers():
        name_provider = provider['name']  # gets name
        tag = '[B][COLOR FF008542][ENABLE] [/COLOR][/B]'
        menu_check = [('Check', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=check&addonid=%s)' %
                       provider['addonid'])]
        menu_enable = ('Disable', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable&addonid=%s)' %
                       provider['addonid'])
        if not provider['enabled']:
            tag = '[B][COLOR FFC40401][DISABLE] [/COLOR][/B]'
            menu_enable = ('Enable', 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable&addonid=%s)' %
                           provider['addonid'])
            menu_check = []
        speed = speed_providers.get(provider['addonid'], '')
        speed_text = ' [%s]' % speed if speed != '' else ''
        list_item = xbmcgui.ListItem(label=tag + name_provider + speed_text)
        icon = provider["thumbnail"]
        fanart = provider["fanart"]
        list_item.setArt({'thumb': icon,
                          'icon': icon,
                          'fanart': fanart})
        if provider['enabled']:
            url = base_url + '?mode=provider&addonid=%s' % provider['addonid']
        else:
            url = ''
        is_folder = False
        list_item.addContextMenuItems(menu_check +
                                      [('Check All',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=check_all)'),
                                       menu_enable,
                                       ('Enable All',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable_all)'),
                                       ('Disable All',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable_all)'),
                                       ('Copy Settings To...',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=copy&addonid=%s)' %
                                        provider['addonid']),
                                       ('Apply default values',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=defaults_all)'),
                                       ('Add-on Settings',
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=settings)')],
                                      replaceItems=True)
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(addon_handle, listing, len(listing))
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)
