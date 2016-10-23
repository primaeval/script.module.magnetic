import logger
from utils import get_setting
from utils import size_int, Magnet

GIGABYTE = 1073741824


# filter results
def apply_filters(results_list):
    # filtered_quality_results = filter_quality(results_list)
    # filtered_size_results = filter_size(filtered_quality_results)
    if get_setting("quality_sort", bool):
        return sort_by_quality(results_list)
    else:
        return results_list


# remove dupes and sort by seeds
def cleanup_results(results_list):
    # nothing found
    if len(results_list) == 0:
        return []

    filtered_list = []
    for result in results_list:
        # noinspection PyBroadException
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

    return sorted(filtered_list, key=lambda r: (float(r['seeds'])), reverse=True)


# apply size filters
def filter_size(results_list):
    # filtered_results = []
    # for result in results_list:
    #     if result['size'] <= int(get_setting("max_size") or 6) * GIGABYTE:
    #         filtered_results.append(result)
    filtered_results = results_list
    return filtered_results


# apply filters for release, video type etc
def filter_quality(results_list):
    return results_list


# apply sorting based on seeds and quality
# noinspection PyBroadException
def sort_by_quality(results_list):
    logger.log.debug("Applying quality sorting")
    for result in results_list:
        try:
            # seeding level
            if int(result['seeds']) > 200:
                result['seeding_level'] = 4
            elif int(result['seeds']) > 150:
                result['seeding_level'] = 3
            elif int(result['seeds']) > 100:
                result['seeding_level'] = 2
            elif int(result['seeds']) > 50:
                result['seeding_level'] = 1
            else:
                result['seeding_level'] = 0

            # seeds/peers ratio
            if float(result['peers']) > 0:
                seed_ratio = float(result['seeds']) / float(result['peers'])
            else:
                seed_ratio = float(result['seeds']) / 1

            if seed_ratio > 2.5:
                result['seeding_ratio'] = 4
            elif seed_ratio > 2:
                result['seeding_ratio'] = 3
            elif seed_ratio > 1.5:
                result['seeding_ratio'] = 2
            elif seed_ratio > 1:
                result['seeding_ratio'] = 1
            else:
                result['seeding_ratio'] = 0

            # hd streams
            if "1080P" in result['name'].upper():
                result['quality'] = 3
                result['hd'] = 1
            elif "720P" in result['name'].upper():
                result['quality'] = 2
                result['hd'] = 1
            else:
                result['quality'] = 1
                result['hd'] = 0
        except:
            pass

    return sorted(results_list, key=lambda r: (r['hd'], r['seeding_ratio'],
                                               r['seeding_level'], r['quality'], r['size'], r['seeds']), reverse=True)
