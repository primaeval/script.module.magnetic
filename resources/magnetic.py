import os
import time
import urlparse
import futures
import json
import xbmc
import filtering
import logger
from utils import notify, get_setting, ADDON_NAME
from urllib import quote_plus, unquote_plus
from utils import get_icon_path, Magnet, size_int

# provider service config
PROVIDER_SERVICE_HOST = "localhost"
PROVIDER_SERVICE_PORT = 65015

provider_results = []
available_providers = 0
request_time = time.clock()


# provider call back with results
def process_provider(self):
    global provider_results
    global available_providers
    parsed = urlparse.urlparse(self.path)
    addonid = urlparse.parse_qs(parsed.query)['addonid'][0]
    content_length = int(self.headers['Content-Length'])
    post_data = self.rfile.read(content_length)
    self._writeheaders()
    self.wfile.write("OK")
    data = json.loads(post_data)
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

    if 'search=' not in parsed.query:
        return []

    operation = urlparse.parse_qs(parsed.query)['search'][0]

    if operation == "general":
        method = "search"
        title = urlparse.parse_qs(parsed.query)['title'][0]
        general_item = {'title': unquote_plus(str(title).replace("'", ""))}
        payload = json.dumps(general_item)

    elif operation == "movie":
        method = "search_movie"
        title = urlparse.parse_qs(parsed.query)['title'][0]
        year = urlparse.parse_qs(parsed.query)['year'][0]
        imdbid = urlparse.parse_qs(parsed.query)['imdb'][0]
        movie_item = {'imdb_id': str(imdbid), 'title': unquote_plus(str(title).replace("'", "")), 'year': str(year)}
        payload = json.dumps(movie_item)

    elif operation == "episode":
        method = "search_episode"
        title = urlparse.parse_qs(parsed.query)['title'][0]
        season = urlparse.parse_qs(parsed.query)['season'][0]
        episode = urlparse.parse_qs(parsed.query)['episode'][0]
        episode_item = {'title': unquote_plus(str(title).replace("'", "")), 'season': int(season),
                        'episode': int(episode), 'absolute_number': int(0)}
        payload = json.dumps(episode_item)

    elif operation == "season":
        method = "search_season"
        title = urlparse.parse_qs(parsed.query)['title'][0]
        season = urlparse.parse_qs(parsed.query)['season'][0]
        season_item = {'title': unquote_plus(str(title).replace("'", "")), 'season': int(season),
                       'absolute_number': int(0)}
        payload = json.dumps(season_item)

    else:
        return json.dumps("OPERATION NOT FOUND")

    normalized_list = search(method, payload)

    logger.log.info("Filtering returned: " + str(len(normalized_list['magnets'])) + " results")
    return json.dumps(normalized_list)


# search for torrents - call providers
def search(method, payloadjson):
    global provider_results
    global available_providers
    global request_time
    request_time = time.clock()
    # collect data
    path = xbmc.translatePath("special://home/addons/")
    addons = os.listdir(path)

    # get magnetic addons
    magnetic_addons = []
    for addon in addons:
        if ("script.%s." % ADDON_NAME.lower()) in addon:
            available_providers += 1
            magnetic_addons.append(addon)

    # return empty list
    if len(magnetic_addons) == 0:
        notify("No providers installed", image=get_icon_path())
        logger.log.info("No providers installed")
        empty_list = {'results': 0, 'time': "0 seconds"}
        return empty_list

    with futures.ThreadPoolExecutor(max_workers=available_providers) as executor:
        # start the load operations and mark each future with its URL
        future_to_addon = {executor.submit(run_provider, addon, method, payloadjson): addon for addon in
                           magnetic_addons}
        for future in futures.as_completed(future_to_addon):
            url = future_to_addon[future]

    providers_time = time.clock()
    # while all providers have not returned results or timeout not reached
    while (time.clock() - providers_time) < (int(get_setting("provider_timeout")) or 30):
        # if all providers have returned results exit
        if available_providers == 0:
            break
        # check every 200ms
        xbmc.sleep(200)
        pass
    logger.log.info("Providers search returned: " + str(len(provider_results)) + " results")

    # sort and remove dupes
    normalized_list = cleanup_results(provider_results)

    # filter magnets and append to results
    filtered_results = {}
    filtered_results['magnets'] = filtering.apply(normalized_list)

    # append number and time on payload
    filtered_results['results'] = len(filtered_results['magnets'])
    filtered_results['duration'] = str("%.1f" % round(time.clock() - request_time, 2)) + " seconds"
    return filtered_results


# run provider script
def run_provider(addon, method, searchquery):
    logger.log.info("Processing:" + addon)
    xbmc.executebuiltin(
        "RunScript(" + addon + "," + addon + "," + method + "," + quote_plus(searchquery.encode('utf-8')) + ")", True)


# remove dupes and sort by seeds
def cleanup_results(results_list):
    # nothing found
    if len(results_list) == 0:
        return []

    filtered_list = []
    for result in results_list:
        try:
            # check provider returns seeds
            int(result['seeds'])

            # size to bytes
            result['size'] = size_int(result['size'])

            # append size label
            if int(result['size']) < 1073741824:
                result['size_label'] = (str(int(result['size'] / 1024 / 1024)) + 'MB')
            else:
                result['size_label'] = (str("%.2f" % (float(result['size']) / 1024 / 1024 / 1024)) + 'GB')

            # append hash
            result['hash'] = Magnet(result['uri']).info_hash.upper()

            # remove dupes
            if len([item for item in filtered_list if item['hash'].upper() == result['hash'].upper()]) == 0:
                # append item to results
                filtered_list.append(result)

        except:
            logger.log.info("Failed to parse:" + str(result))
            pass

    return sorted(filtered_list, key=lambda result: (float(result['seeds'])), reverse=True)
