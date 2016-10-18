import urlparse
from threading import Thread
from urllib import quote_plus, unquote_plus

import xbmc

import filtering
import logger
from storage import *
from utils import get_icon_path
from utils import notify, get_setting

provider_results = []
available_providers = 0
request_time = time.clock()

# cache of 6h
storage_info = Storage(xbmc.translatePath('special://profile/addon_data/script.module.magnetic/'), 60 * 6)


# provider call back with results
def process_provider(self):
    global provider_results
    global available_providers
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
    database = storage_info["providers"]
    cache = database.get(payload, None)
    if cache is None:
        normalized_list = search(method, payload, provider)
        database[payload] = normalized_list
        database.sync()
    else:
        normalized_list = cache

    logger.log.info("Filtering returned: " + str(len(normalized_list.get('magnets', []))) + " results")
    return json.dumps(normalized_list)


# search for torrents - call providers
def search(method, payload_json, provider=""):
    global provider_results
    global available_providers
    global request_time
    request_time = time.clock()
    # collect data
    if len(provider) == 0:
        addons = os.listdir(xbmc.translatePath("special://home/addons/"))
    else:
        addons = [provider]

    # get magnetic addons
    magnetic_addons = []
    for addon in addons:
        if "script.magnetic." in addon:
            available_providers += 1
            task = Thread(target=run_provider, args=(addon, method, payload_json))
            task.start()
            magnetic_addons.append(addon)

    # return empty list
    if len(magnetic_addons) == 0:
        notify("No providers installed", image=get_icon_path())
        logger.log.info("No providers installed")
        empty_list = {'results': 0, 'time': "0 seconds"}
        return empty_list

    providers_time = time.clock()
    # while all providers have not returned results or timeout not reached
    while (time.clock() - providers_time) < (int(get_setting("provider_timeout")) or 60):
        # if all providers have returned results exit
        if available_providers == 0:
            break
        # check every 1000ms
        xbmc.sleep(1000)

    # filter magnets and append to results
    filtered_results = dict(magnets=filtering.apply_filters(provider_results))

    # append number and time on payload
    filtered_results['results'] = len(filtered_results['magnets'])
    filtered_results['duration'] = str("%.1f" % round(time.clock() - request_time, 2)) + " seconds"
    logger.log.info(
        "Providers search returned: %s results in %s" % (str(len(provider_results)), filtered_results['duration']))
    return filtered_results


# run provider script
def run_provider(addon, method, search_query):
    logger.log.info("Processing:" + addon)
    xbmc.executebuiltin(
        "RunScript(" + addon + "," + addon + "," + method + "," + quote_plus(search_query.encode('utf-8')) + ")", True)
