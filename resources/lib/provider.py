# -*- coding: utf-8 -*-
# This code is based in provider.py from pulsar
# https://github.com/steeve/plugin.video.pulsar

import re
import sys
import urllib2
from cookielib import CookieJar, LWPCookieJar
from os import path
from time import sleep
from urllib import unquote_plus, urlencode, quote, quote_plus
from urlparse import urlparse

import xbmcaddon

from ehp import *
from storage import *
from utils import PROVIDER_SERVICE_HOST, PROVIDER_SERVICE_PORT
from utils import get_setting, get_int, get_float, notify

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36" \
             " (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"
Html()
COOKIES = CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(COOKIES)))


# noinspection PyBroadException
def register(search, search_movie, search_episode, search_season):
    if len(sys.argv) < 4:
        xbmcaddon.Addon().openSettings()
        return
    query = json.loads(unquote_plus(sys.argv[3]))
    method = sys.argv[2]
    addonid = sys.argv[1]
    method = {
        "search": search,
        "search_movie": search_movie,
        "search_episode": search_episode,
        "search_season": search_season
    }.get(method)

    # post to service magnet results
    callback = "http://" + str(PROVIDER_SERVICE_HOST) + ":" + str(
        PROVIDER_SERVICE_PORT) + "/providers?addonid=%s" % str(addonid)
    try:
        results = list(method(query))
        results = json.dumps(results)

    except:
        results = json.dumps([])
        logger.log.error("Addon threw error:" + str(addonid))

    request_url = urllib2.Request(callback, results)
    urllib2.urlopen(request_url, timeout=60)


# provider web browser with cookies management
class Browser:
    def __init__(self):
        pass

    _cookies = None
    cookies = LWPCookieJar()
    content = None
    status = None
    headers = dict()

    @classmethod
    def create_cookies(cls, payload):

        cls._cookies = urlencode(payload)

    # to open any web page
    @classmethod
    def open(cls, url='', language='en', post_data=None, get_data=None):
        if post_data is None:
            post_data = {}
        if get_data is not None:
            url += '?' + urlencode(get_data)
        logger.log.debug(url)
        result = True
        if len(post_data) > 0:
            cls.create_cookies(post_data)
        if cls._cookies is not None:
            req = urllib2.Request(url, cls._cookies)
            cls._cookies = None
        else:
            req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Content-Language', language)
        req.add_header("Accept-Encoding", "gzip")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cls.cookies))  # open cookie jar
        try:
            sleep(0.5)  # good spider
            response = opener.open(req)  # send cookies and open url
            cls.headers = response.headers
            # borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                cls.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                cls.content = response.read()
            response.close()
            cls.status = 200
            logger.log.debug("Status: " + str(cls.status))
            logger.log.debug(cls.content)
        except urllib2.HTTPError as e:
            cls.status = e.code
            logger.log.warning("Status: " + str(cls.status))
            result = False
            if e.code == 503:
                # trying to open with antibots tool
                sleep(0.5)  # good spider
                import cfscrape
                scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
                cls.content = scraper.get(url).content
                cls.status = 200
                notify("Antibot's  measure for %s" % url)
                logger.log.warning("Trying antibot's measure")
                result = True
        except urllib2.URLError as e:
            cls.status = e.reason
            logger.log.warning("Status: " + str(cls.status))
            if '[Errno 1]' in cls.status:
                notify('obsolete Kodi version to open %s' % url)
            result = False
        return result

    # alternative when it is problem with https
    @classmethod
    def open2(cls, url=''):
        import httplib

        word = url.split("://")
        pos = word[1].find("/")
        conn = httplib.HTTPConnection(re.search[:pos])
        conn.request("GET", re.search[pos:])
        r1 = conn.getresponse()
        cls.status = str(r1.status) + " " + r1.reason
        cls.content = r1.read()
        if r1.status == 200:
            return True
        else:
            return False

    # used for sites with login
    @classmethod
    def login(cls, url, payload, word):
        result = False
        cls.create_cookies(payload)
        if cls.open(url):
            result = True
            data = cls.content
            if word in data:
                cls.status = 'Wrong Username or Password'
                result = False
        return result


# find the name in different language
def translator(title, imdb_id, language, extra=True):
    keywords = {'en': '', 'de': '', 'es': 'espa', 'fr': 'french', 'it': 'italian', 'pt': 'portug'}
    if len(imdb_id) > 0:
        url_themoviedb = "http://api.themoviedb.org/3/find/%s?api_key=8d0e4dca86c779f4157fc2c469c372ca&language=%s" \
                         "&external_source=imdb_id" % (imdb_id, language)
        if Browser.open(url_themoviedb):
            results = json.loads(Browser.content)
            if len(results['movie_results']) > 0:
                title = results['movie_results'][0]['title'].encode('utf-8')
                original_title = results['movie_results'][0]['original_title'].encode('utf-8')
            elif len(results['tv_results']) > 0:
                title = results['tv_results'][0]['name'].encode('utf-8')
                original_title = results['tv_results'][0]['original_name'].encode('utf-8')
            else:
                title = ""
                original_title = ""
            if title == original_title and extra:
                title += ' ' + keywords[language]
        else:
            title = 'Pas de communication avec le themoviedb.org'
    else:
        url_themoviedb = "http://api.themoviedb.org/3/search/tv?api_key=8d0e4dca86c779f4157fc2c469c372ca" \
                         "&query=%s&language=%s" % (title.replace(' ', '+'), language)
        if Browser.open(url_themoviedb):
            results = json.loads(Browser.content)
            if len(results['results']) > 0:
                title = results['results'][0]['name']
                original_title = results['results'][0]['original_name']
                if title == original_title and extra:
                    title += ' ' + keywords[language]
        else:
            title = 'Pas de communication avec le themoviedb.org'
    return Filtering.safe_name(title.rstrip())


#  Get the title from imdb id code
def imdb_title(imdb_id):
    result = ''
    if Browser.open('http://www.omdbapi.com/?i=%s&r=json' % imdb_id):
        data = Browser.content.replace('"', '').replace('{', '').replace('}', '').split(',')
        result = data[0].split(":")[1] + ' ' + data[1].split(":")[1]
    return result


def clean_size(text=""):
    if text is not None:
        pos = text.rfind('B')
        if pos > 0:
            text = text[:pos] + 'B'
    return text


def add_base_url(url=''):
    if url.startswith('//'):
        url = 'http:' + url
    elif url.startswith('/'):
        if Settings.url.endswith('/'):
            url = Settings.url + url[1:]
        else:
            url = Settings.url + url
    return url


def clean_magnet(magnet="", info_hash=""):
    if len(magnet) > 0:
        magnet = add_base_url(magnet)
    elif len(magnet) == 0 and len(info_hash) > 0:
        magnet = 'magnet:?xt=urn:btih:%s' % info_hash
    return magnet


# get the first magnet or torrent from one webpage
def get_links(page):
    result = ''
    if page is not None:
        page = add_base_url(page)
        if Browser.open(quote(page).replace("%3A", ":")):
            content = re.findall('magnet:\?[^\'"\s<>\[\]]+', Browser.content)
            if content is not None and len(content) > 0:
                result = content[0]
            else:
                content = re.findall('http(.*?).torrent', Browser.content)
                if content is not None and len(content) > 0:
                    result = 'http' + content[0] + '.torrent'
    return result


# noinspection PyBroadException
def get_playable_link(page):
    page = normalize_string(page)
    exceptions_list = Storage.open("exceptions")
    result = page
    logger.log.debug(result)
    if 'divxatope' in page:
        page = page.replace('/descargar/', '/torrent/')
        result = page
    is_link = True
    logger.log.debug(exceptions_list.items())
    if exceptions_list.has(result):
        return page
    if page.startswith("http") and is_link:
        # exceptions
        logger.log.debug(result)
        # download page
        try:
            Browser.open(page)
            data = normalize_string(Browser.content)
            logger.log.debug(Browser.headers)
            if 'text/html' in Browser.headers.get("content-type", ""):
                content = re.findall('magnet:\?[^\'"\s<>\[\]]+', data)
                if content is not None and len(content) > 0:
                    result = content[0]
                else:
                    content = re.findall('/download\?token=[A-Za-z0-9%]+', data)
                    if content is not None and len(content) > 0:
                        result = Settings["url_address"] + content[0]
                    else:
                        content = re.findall('/telechargement/[a-z0-9-_.]+', data)  # cpasbien
                        if content is not None and len(content) > 0:
                            result = Settings["url_address"] + content[0]
                        else:
                            content = re.findall('https?:[^\'"\s<>\[\]]+torrent', data)
                            if content is not None and len(content) > 0:
                                result = content[0]
            else:
                exceptions_list.add(re.search("^https?://(.*?)/", page).group(1))
                exceptions_list.sync()
        except:
            pass
    logger.log.info(result)
    return quote_plus(page)


def parse_json(data):
    import json
    return json.loads(data)


def parse_xml(data):
    import xml.etree.ElementTree as eT
    return eT.fromstring(data)


def exception(title):
    title = title.lower()
    title = title.replace('csi crime scene investigation', 'CSI')
    title = title.replace('law and order special victims unit', 'law and order svu')
    title = title.replace('law order special victims unit', 'law and order svu')
    return title


def read_keywords(keywords):
    results = []
    for value in re.findall('{(.*?)}', keywords):
        results.append(value)
    return results


def format_decimal(times):
    value = ''
    for i in range(1, times):
        value += '0'
    return "%" + value + "%sd" % times


# read provider xbmcaddon.Addon()
class MetaSettings(type):
    @classmethod
    def __getitem__(mcs, item):
        if item is "max_magnets":
            return get_int(mcs.value.get(item, "10"))
        elif item is "separator":
            return mcs.value.get(item, "%20")
        elif item is "notification":
            return get_int(mcs.value.get(item, "50"))
        elif item.endswith("accept"):
            temp = mcs.value.get(item, "{*}")
            return "{*}" if temp is "" else temp
        elif item.endswith("max_size"):
            return get_float(mcs.value.get(item, "10"))
        elif item.endswith("min_size"):
            return get_float(mcs.value.get(item, "0"))
        elif item.endswith("_title"):
            return mcs.value.get(item, "true")
        elif item.endswith("read_magnet_link"):
            return mcs.value.get(item, "false")
        else:
            return mcs.value.get(item, "")

    # General information
    idAddon = xbmcaddon.Addon().getAddonInfo('ID')  # gets name
    icon = xbmcaddon.Addon().getAddonInfo('icon')
    fanart = xbmcaddon.Addon().getAddonInfo('fanart')
    path_folder = xbmcaddon.Addon().getAddonInfo('path')
    name = xbmcaddon.Addon().getAddonInfo('name')  # gets name
    name_provider = re.sub('.COLOR (.*?)]', '', name.replace('[/COLOR]', ''))
    value = {}  # it contains all the settings from xml file
    fileName = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(fileName):
        with open(fileName, 'r') as fp:
            data = fp.read()
        for key in re.findall('id="(\w+)"', data):
            value[key] = get_setting(key)  # reading the values from xbmcaddon.Addon().xml
    temp = urlparse(value.get('general_url', ""))
    url = '%s://%s' % (temp.scheme, temp.netloc)


class Settings(object):
    def __init__(self):
        pass

    __metaclass__ = MetaSettings
    pass


# filtering
class Filtering:
    def __init__(self):
        pass

    info = dict(title="")
    post_data = {}
    get_data = None
    reason = ''
    title = ''
    results = []
    url = ''
    filter_title = 'true'
    quality_allow = read_keywords(Settings["general_accept"])
    quality_deny = read_keywords(Settings["general_block"])
    min_size = Settings["general_min_size"]
    max_size = Settings["general_max_size"]
    queries = [Settings["general_query1"],
               Settings["general_query2"],
               Settings["general_query3"],
               Settings["general_query4"],
               Settings["general_query5"]]

    @classmethod
    def use_general(cls, info):
        cls.info = info
        cls.url = Settings["general_url"]
        cls.filter_title = Settings["general_title"]
        cls.quality_allow = read_keywords(Settings["general_accept"])
        cls.quality_deny = read_keywords(Settings["general_block"])
        cls.min_size = Settings["general_min_size"]
        cls.max_size = Settings["general_max_size"]
        cls.queries = [Settings["general_query1"],
                       Settings["general_query2"],
                       Settings["general_query3"],
                       Settings["general_query4"],
                       Settings["general_query5"]]

    @classmethod
    def use_movie(cls, info):
        cls.info = info
        cls.url = Settings["movie_url"]
        cls.filter_title = Settings["movie_title"]
        cls.quality_allow = read_keywords(Settings["movie_accept"])
        cls.quality_deny = read_keywords(Settings["movie_block"])
        cls.min_size = Settings["movie_min_size"]
        cls.max_size = Settings["movie_max_size"]
        cls.queries = [Settings["movie_query1"],
                       Settings["movie_query2"],
                       Settings["movie_query3"],
                       Settings["movie_query4"],
                       Settings["movie_query5"]]

    @classmethod
    def use_tv(cls, info):
        cls.info = info
        cls.url = Settings["tv_url"]
        cls.filter_title = Settings["tv_title"]
        cls.quality_allow = read_keywords(Settings["tv_accept"])
        cls.quality_deny = read_keywords(Settings["tv_block"])
        cls.min_size = Settings["tv_min_size"]
        cls.max_size = Settings["tv_max_size"]
        cls.queries = [Settings["tv_query1"],
                       Settings["tv_query2"],
                       Settings["tv_query3"],
                       Settings["tv_query4"],
                       Settings["tv_query5"]]

    @classmethod
    def use_season(cls, info):
        cls.info = info
        cls.url = Settings["season_url"]
        cls.filter_title = Settings["season_title"]
        cls.quality_allow = read_keywords(Settings["season_accept"])
        cls.quality_deny = read_keywords(Settings["season_block"])
        cls.min_size = Settings["season_min_size"]
        cls.max_size = Settings["season_max_size"]
        cls.queries = [Settings["season_query1"],
                       Settings["season_query2"],
                       Settings["season_query3"],
                       Settings["season_query4"],
                       Settings["season_query5"]]

    @classmethod
    def use_anime(cls, info):
        cls.info = info
        cls.url = Settings["anime_url"]
        cls.filter_title = Settings["anime_title"]
        cls.quality_allow = read_keywords(Settings["anime_accept"])
        cls.quality_deny = read_keywords(Settings["anime_block"])
        cls.min_size = Settings["anime_min_size"]
        cls.max_size = Settings["anime_max_size"]
        cls.queries = [Settings["anime_query1"],
                       Settings["anime_query2"],
                       Settings["anime_query3"],
                       Settings["anime_query4"],
                       Settings["anime_query5"]]

    @classmethod
    def information(cls):
        logger.log.debug('Accepted Keywords: %s' % cls.quality_allow)
        logger.log.debug('Blocked Keywords: %s' % cls.quality_deny)
        logger.log.debug('min Size: %s' % str(cls.min_size) + ' GB')
        logger.log.debug('max Size: %s' % ((str(cls.max_size) + ' GB') if cls.max_size != 10 else 'MAX'))

    # validate keywords
    @staticmethod
    def included(value, keys, strict=False):
        value = ' ' + value + ' '
        if '*' in keys:
            res = True
        else:
            res1 = []
            for key in keys:
                res2 = []
                for item in re.split('\s', key):
                    item = item.replace('?', ' ').replace('_', ' ')
                    if strict:
                        item = ' ' + item + ' '  # it makes that strict the comparation
                    if item.upper() in value.upper():
                        res2.append(True)
                    else:
                        res2.append(False)
                res1.append(all(res2))
            res = any(res1)
        return res

    # validate size
    @classmethod
    def size_clearance(cls, size):
        max_size1 = 100 if cls.max_size == 10 else cls.max_size
        res = False
        value = get_float(size)
        value *= 0.001 if 'M' in size else 1
        if cls.min_size <= value <= max_size1:
            res = True
        return res

    # noinspection PyBroadException
    @staticmethod
    def normalize_string(name):
        from unicodedata import normalize
        import types
        try:
            normalize_name = name.decode('unicode-escape').encode('latin-1')
        except:
            if types.StringType == type(name):
                unicode_name = unicode(name, 'utf-8', 'ignore')
            else:
                unicode_name = name
            normalize_name = normalize('NFKD', unicode_name).encode('ascii', 'ignore')
        return normalize_name

    @staticmethod
    def un_code_name(name):  # convert all the &# codes to char, remove extra-space and normalize
        from HTMLParser import HTMLParser

        name = name.replace('<![CDATA[', '').replace(']]', '')
        name = HTMLParser().unescape(name.lower())
        return name

    @staticmethod
    def unquote_name(name):  # convert all %symbols to char
        from urllib import unquote

        return unquote(name)

    @classmethod
    def safe_name(cls, value):  # make the name directory and filename safe
        value = cls.normalize_string(value)  # First normalization
        value = cls.unquote_name(value)
        value = cls.un_code_name(value)
        value = cls.normalize_string(
            value)  # Last normalization, because some unicode char could appear from the previous steps
        value = value.lower().title()
        keys = {'"': ' ', '*': ' ', '/': ' ', ':': ' ', '<': ' ', '>': ' ', '?': ' ', '|': ' ', '_': ' ',
                "'": '', 'Of': 'of', 'De': 'de', '.': ' ', ')': ' ', '(': ' ', '[': ' ', ']': ' ', '-': ' '}
        for key in keys.keys():
            value = value.replace(key, keys[key])
        value = ' '.join(value.split())
        return value.replace('S H I E L D', 'SHIELD')

    # verify
    @classmethod
    def verify(cls, name, size):
        if name is None or name is '':
            cls.reason = name.replace(' - ' + Settings.name_provider, '') + ' ***Empty Name***'
            return False
        name = cls.safe_name(name)
        cls.title = cls.safe_name(cls.title) if cls.filter_title in 'true' else name
        normalized_title = cls.normalize_string(cls.title)  # because sometimes there are missing accents in the results
        cls.reason = name.replace(' - ' + Settings.name_provider, '') + ' ***Blocked File by'
        list_to_verify = [cls.title, normalized_title] if cls.title != normalized_title else [cls.title]
        if cls.included(name, list_to_verify, True):
            result = True
            if name is not None:
                if not cls.included(name, cls.quality_allow):
                    cls.reason += ", Missing Accepted Keyword"
                    result = False
                if cls.included(name, cls.quality_deny):
                    cls.reason += ", Blocked Keyword"
                    result = False
            if size is not None and size is not '':
                if not cls.size_clearance(size):
                    result = False
                    cls.reason += ", Size"
        else:
            result = False
            cls.reason += ", Name"
        cls.reason = cls.reason.replace('by,', 'by') + '***'
        return result


class Magnet:
    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(.*?)&', self.magnet)
        result = ''
        if info_hash is not None:
            result = info_hash.group(1)
        self.hash = result
        # name
        name = re.search('dn=(.*?)&', self.magnet)
        result = ''
        if name is not None:
            result = name.group(1).replace('+', ' ')
        self.name = result.title()
        # trackers
        self.trackers = re.findall('tr=(.*?)&', self.magnet)


def generate_payload(generator=None, verify_name=True, verify_size=True):
    Filtering.information()  # print filters xbmcaddon.Addon()
    results = []
    cont = 0
    for name, info_hash, magnet, size, seeds, peers in generator:
        size = clean_size(size)
        magnet = clean_magnet(magnet, info_hash)
        v_name = name if verify_name else Filtering.title
        v_size = size if verify_size else None
        logger.log.debug("name: %s \n info_hash: %s\n magnet: %s\n size: %s\n seeds: %s\n peers: %s" % (
            name, info_hash, magnet, size, seeds, peers))
        if Filtering.verify(v_name, v_size):
            cont += 1
            if Settings["read_magnet_link"] == "true":
                magnet = get_links(magnet)  # magnet
            results.append({"name": name,
                            "uri": magnet,
                            "info_hash": info_hash,
                            "size": size,
                            "seeds": get_int(seeds),
                            "peers": get_int(peers),
                            "language": Settings["language"],
                            "provider": Settings.name,
                            "icon": Settings.icon,
                            })  # return the torrent
            if cont >= Settings["max_magnets"]:  # limit magnets
                break
        else:
            logger.log.debug(Filtering.reason)
    logger.log.debug('>>>>>>' + str(cont) + ' torrents sent to Magnetic<<<<<<<')
    return results


def process(generator=None, verify_name=True, verify_size=True):
    from threading import Thread
    threads = []

    t = Thread(target=execute_process, args=(generator, verify_name, verify_size))
    threads.append(t)

    # Start all threads
    for x in threads:
        x.start()

    # Wait for all of them to finish
    for x in threads:
        x.join()

    return Filtering.results


def execute_process(generator=None, verify_name=True, verify_size=True):
    for query in Filtering.queries:
        keywords = read_keywords(query)
        for keyword in keywords:
            keyword = keyword.lower()
            if 'title' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    logger.log.debug(Filtering.info)
                    title = translator(Filtering.info['title'], Filtering.info.get('imdb_id', ''), keys[1], False)
                else:
                    title = Filtering.info["title"].encode('utf-8')
                query = query.replace('{%s}' % keyword, title)
            if 'year' in keyword:
                query = query.replace('{%s}' % keyword, Filtering.info["year"])
            if 'season' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    season = format_decimal(get_int(keys[1])) % Filtering.info["season"]
                else:
                    season = '%s' % Filtering.info["season"]
                query = query.replace('{%s}' % keyword, '' + season)
            if 'episode' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    episode = format_decimal(get_int(keys[1])) % Filtering.info["episode"]
                else:
                    episode = '%s' % Filtering.info["episode"]
                query = query.replace('{%s}' % keyword, '' + episode)
        if query is not '':
            # creating url
            url_search = Filtering.url.replace('QUERY', query.replace(' ', Settings['separator']))
            # creating the payload for Post Method
            payload = dict()
            for key, value in Filtering.post_data.iteritems():
                if 'QUERY' in value:
                    payload[key] = Filtering.post_data[key].replace('QUERY', query)
                else:
                    payload[key] = Filtering.post_data[key]
            logger.log.debug(query)
            logger.log.debug(Filtering.post_data)
            logger.log.debug(payload)
            # creating the payload for Get Method
            data = None
            if Filtering.get_data is not None:
                data = dict()
                for key, value in Filtering.get_data.iteritems():
                    if 'QUERY' in value:
                        data[key] = Filtering.get_data[key].replace('QUERY', query)
                    else:
                        data[key] = Filtering.get_data[key]
            Filtering.title = query  # to do filtering by name
            logger.log.debug(url_search)
            Browser.open(url_search, post_data=payload, get_data=data)
            Filtering.results.extend(generate_payload(generator(Browser.content), verify_name, verify_size))
