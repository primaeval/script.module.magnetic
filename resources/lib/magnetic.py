# coding: utf-8
import urlparse
from threading import Thread
from urllib import quote_plus, unquote_plus

import filtering
from storage import *
from utils import *

provider_results = []
provider_name = []
available_providers = 0
request_time = time.clock()


# provider call back with results
def process_provider(self):
    global provider_results
    global available_providers
    global provider_name
    parsed = urlparse.urlparse(self.path)
    addonid = urlparse.parse_qs(parsed.query)['addonid'][0]
    content_length = int(self.headers['Content-Length'])
    payload = self.rfile.read(content_length)
    self._write_headers()
    self.wfile.write("OK")
    data = json.loads(payload)
    logger.log.info("Provider " + addonid + " returned " + str(len(data)) + " results in " + str(
        "%.1f" % round(time.clock() - request_time, 2)) + " seconds")
    if len(data) > 0:
        if len(provider_results) == 0:
            provider_results = data
        else:
            for item in data:
                provider_results.append(item)
    available_providers -= 1
    provider_name.remove(addonid)


def get_results(self):
    global provider_results

    # init list
    provider_results = []

    # request data
    parsed = urlparse.urlparse(self.path)

    info = urlparse.parse_qs(parsed.query)
    operation = info.get('search', [''])[0]
    provider = info.get('provider', [''])[0]
    title = unquote_plus(str(info.get('title', [''])[0]).replace("'", ""))

    if operation == 'general':
        method = 'search'
        general_item = {'title': title}
        payload = json.dumps(general_item)

    elif operation == "movie":
        method = "search_movie"
        year = info.get('year', [''])[0]
        imdb_id = info.get('imdb', [''])[0]
        movie_item = {'imdb_id': str(imdb_id),
                      'title': title,
                      'year': str(year)}
        payload = json.dumps(movie_item)

    elif operation == "episode":
        method = "search_episode"
        season = info.get('season', [''])[0]
        episode = info.get('episode', [''])[0]
        episode_item = {'title': title,
                        'season': int(season),
                        'episode': int(episode),
                        'absolute_number': int(0)}
        payload = json.dumps(episode_item)

    elif operation == "season":
        method = "search_season"
        season = info.get('season', [''])[0]
        season_item = {'title': title,
                       'season': int(season),
                       'absolute_number': int(0)}
        payload = json.dumps(season_item)

    else:
        return json.dumps("OPERATION NOT FOUND")

    if len(title) == 0 or len(method) == 0:
        return json.dumps("Payload Incomplete!!!      ") + payload

    # check if the search is in cache
    database = Storage.open("providers", 60 * 6, True)
    cache = database.get(payload, None)

    if cache is None or not get_setting('use_cache', bool) or len(provider) > 0:
        normalized_list = search(method, payload, provider)
        results = normalized_list
        # if there is results it will be saved in cache
        if len(normalized_list.get('magnets', [])) > 0:
            database[payload] = results
            database.sync()
    else:
        normalized_list = cache
        display_message_cache()

    logger.log.info("Filtering returned: " + str(len(normalized_list.get('magnets', []))) + " results")
    return json.dumps(normalized_list)


# search for torrents - call providers
def search(method, payload_json, provider=""):
    global provider_results
    global available_providers
    global request_time
    global provider_name

    # reset global variables
    provider_results = []
    provider_name = []
    available_providers = 0
    request_time = time.clock()

    # collect data
    if len(provider) == 0:
        addons = get_list_providers_enabled()
    else:
        addons = [provider]

    if len(addons) == 0:
        # return empty list
        notify(string(32060), image=get_icon_path())
        logger.log.info("No providers installed")
        return {'results': 0, 'duration': "0 seconds", 'magnets': []}

    p_dialog = xbmcgui.DialogProgressBG()
    p_dialog.create('Magnetic Manager', string(32061))

    for addon in addons:
        available_providers += 1
        provider_name.append(addon)
        task = Thread(target=run_provider, args=(addon, method, payload_json))
        task.start()

    providers_time = time.clock()
    total = float(available_providers)

    # while all providers have not returned results or timeout not reached
    time_out = min(get_setting("timeout", int), 60)

    # if all providers have returned results exit
    # check every 100ms
    while time.clock() - providers_time < time_out and available_providers > 0:
        xbmc.sleep(100)
        message = string(32062) % available_providers if available_providers > 1 else string(32063)
        p_dialog.update(int((total - available_providers) / total * 100), message=message)

    # time-out provider
    if len(provider_name) > 0:
        message = ', '.join(provider_name)
        message = message.replace('script.magnetic.', '').title() + string(32064)
        logger.log.info(message)
        notify(message, ADDON_ICON)

    # filter magnets and append to results
    filtered_results = dict(magnets=filtering.apply_filters(provider_results))

    # append number and time on payload
    filtered_results['results'] = len(filtered_results['magnets'])
    filtered_results['duration'] = str("%.1f" % round(time.clock() - request_time, 2)) + " seconds"
    logger.log.info(
        "Providers search returned: %s results in %s" % (str(len(provider_results)), filtered_results['duration']))

    # destroy notification object
    p_dialog.close()
    del p_dialog

    return filtered_results


# run provider script
def run_provider(addon, method, search_query):
    logger.log.debug("Processing:" + addon)
    xbmc.executebuiltin(
        "RunScript(" + addon + "," + addon + "," + method + "," + quote_plus(search_query.encode('utf-8')) + ")", True)
