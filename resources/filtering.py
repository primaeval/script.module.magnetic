import logger
from utils import get_setting

GIGABYTE = 1073741824

# filter results
def apply(results_list):
    filtered_quality_results = filter_quality(results_list)
    filtered_size_results = filter_size(filtered_quality_results)
    if get_setting("quality_sort", bool):
        return sort_by_quality(filtered_size_results)
    else:
        return filtered_size_results


# apply size filters
def filter_size(results_list):
    filtered_results = []
    for result in results_list:
        if result['size'] <= int(get_setting("max_size") or 6) * GIGABYTE:
            filtered_results.append(result)

    return filtered_results


# apply filters for release, video type etc
def filter_quality(results_list):
    return results_list


# apply sorting based on seeds and quality
def sort_by_quality(results_list):
    logger.log.info("Applying quality sorting")
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
                seedratio = float(result['seeds']) / float(result['peers'])
            else:
                seedratio = float(result['seeds']) / 1

            if seedratio > 2.5:
                result['seeding_ratio'] = 4
            elif seedratio > 2:
                result['seeding_ratio'] = 3
            elif seedratio > 1.5:
                result['seeding_ratio'] = 2
            elif seedratio > 1:
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

    return sorted(results_list, key=lambda result: (result['hd'], result['seeding_ratio'], result['seeding_level'], result['quality'], result['size'], result['seeds']), reverse=True)
