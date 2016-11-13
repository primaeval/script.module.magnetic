import logger
from utils import Magnet, get_float


# filter results
def apply_filters(results_list):
    logger.log.debug(results_list)
    results_list = cleanup_results(results_list)
    logger.log.debug(results_list)
    results_list = sort_by_quality(results_list)
    logger.log.debug(results_list)
    return results_list


# remove dupes and sort by seeds
def cleanup_results(results_list):
    # nothing found
    if len(results_list) == 0:
        return []

    filtered_list = []
    for result in results_list:
        # check provider returns seeds
        # get_int(result['seeds'])

        # append hash
        result['hash'] = Magnet(result['uri']).info_hash.upper()
        logger.log.debug(result['hash'])

        # remove dupes
        # noinspection PyTypeChecker
        if len([item for item in filtered_list if item['hash'].upper() == result['hash'].upper()]) == 0 or len(
                result['hash']) == 0:
            # append item to results
            filtered_list.append(result)

    return sorted(filtered_list, key=lambda r: (get_float(r['seeds'])), reverse=True)


def check_quality(text=""):
    # quality
    key_words = {"Cam": ["camrip", "cam"],
                 "Telesync": ["ts", "telesync", "pdvd"],
                 "Workprint": ["wp", "workprint"],
                 "Telecine": ["tc", "telecine"],
                 "Pay-Per-View Rip": ["ppv", "ppvrip"],
                 "Screener": ["scr", "screener", "screeener", "dvdscr", "dvdscreener", "bdscr"],
                 "DDC": ["ddc"],
                 "R5": ["r5", "r5.line", "r5 ac3 5 1 hq"],
                 "DVD-Rip": ["dvdrip", "dvd-rip"],
                 "DVD-R": ["dvdr", "dvd-full", "full-rip", "iso rip", "lossless rip", "untouched rip", "dvd-5 dvd-9"],
                 "HDTV": ["dsr", "dsrip", "dthrip", "dvbrip", "hdtv", "pdtv", "tvrip", "hdtvrip", "hdrip", "hdit",
                          "high definition"],
                 "VODRip": ["vodrip", "vodr"],
                 "WEB-DL": ["webdl", "web dl", "web-dl"],
                 "WEBRip": ["web-rip", "webrip", "web rip"],
                 "WEBCap": ["web-cap", "webcap", "web cap"],
                 "BD/BRRip": ["bdrip", "brrip", "blu-ray", "bluray", "bdr", "bd5", "bd", "blurip"],
                 "MicroHD": ["microhd"],
                 "FullHD": ["fullhd"],
                 "BR-Line": ["br line"],
                 # video formats
                 "x264": ["x264", "x 264"],
                 "x265 HEVC": ["x265 hevc", "x265", "x 265", "hevc"],
                 # audio
                 "DD5.1": ["dd5 1", "dd51", "dual audio 5"],
                 "AC3 5.1": ["ac3"],
                 "ACC": ["acc"],
                 "DUAL AUDIO": ["dual", "dual audio"],
                 }
    color = {"Cam": "FFF4AE00",
             "Telesync": "FFF4AE00",
             "Workprint": "FFF4AE00",
             "Telecine": "FFF4AE00",
             "Pay-Per-View Rip": "FFD35400",
             "Screener": "FFD35400",
             "DDC": "FFD35400",
             "R5": "FFD35400",
             "DVD-Rip": "FFD35400",
             "DVD-R": "FFD35400",
             "HDTV": "FFD35400",
             "VODRip": "FFD35400",
             "WEB-DL": "FFD35400",
             "WEBRip": "FFD35400",
             "WEBCap": "FFD35400",
             "BD/BRRip": "FFD35400",
             "MicroHD": "FFD35400",
             "FullHD": "FFD35400",
             "BR-Line": "FFD35400",
             # video formats
             "x264": "FFFB0C06",
             "x265 HEVC": "FFFB0C06",
             # audio
             "DD5.1": "FF089DE3",
             "AC3 5.1": "FF089DE3",
             "ACC": "FF089DE3",
             "DUAL AUDIO": "FF089DE3",
             }
    quality = "480p"
    text_quality = ""
    for key in key_words:
        for keyWord in key_words[key]:
            if ' ' + keyWord + ' ' in ' ' + text + ' ':
                quality = "480p"
                text_quality += " [COLOR %s][%s][/COLOR]" % (color[key], key)

    if "480p" in text:
        quality = "480p"
    if "720p" in text:
        quality = "720p"
    if "1080p" in text:
        quality = "1080p"
    if "3d" in text:
        quality = "1080p"
    if "4k" in text:
        quality = "2160p"
    return quality


# apply sorting based on seeds and quality
# noinspection PyBroadException
def sort_by_quality(results_list):
    logger.log.debug("Applying quality sorting")
    for result in results_list:
        # hd streams
        quality = check_quality(result['name'])
        if "1080p" in quality:
            result['quality'] = 3
            result['hd'] = 1
        elif "720p" in quality:
            result['quality'] = 2
            result['hd'] = 1
        else:
            result['quality'] = 1
            result['hd'] = 0

    return sorted(results_list, key=lambda r: (r["seeds"], r['hd'], r['quality'], r["peers"]), reverse=True)
