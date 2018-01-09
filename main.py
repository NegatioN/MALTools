#!/usr/bin/env python3
from malparser import MAL
import requests
from xml.etree import cElementTree as ET
from pprint import pprint
import time
import json
import os
from tqdm import tqdm

username = 'NegatioN'
sleep = 0.5
save_path = 'mydata.json'

mal = MAL()

STATUS_NAMES = {
    1: 'watching',
    2: 'completed',
    3: 'on hold',
    4: 'dropped',
    6: 'plan to watch',  # not a typo
    7: 'rewatching'  # this not exists in API
}

USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/34.0.1847.116 Safari/537.36')

## Shamelessly stolen from https://github.com/ryukinix/mal
def anime_list(username, status='all', type='anime', stats=False):

    payload = dict(u=username, status=status, type=type)
    r = requests.get(
        'http://myanimelist.net/malappinfo.php',
        params=payload,
        headers={'User-Agent': USER_AGENT}
    )
    if "_Incapsula_Resource" in r.text:
        raise RuntimeError("Request blocked by Incapsula protection")

    result = dict()
    for raw_entry in ET.fromstring(r.text):
        entry = dict((attr.tag, attr.text) for attr in raw_entry)

        # anime information
        if 'series_animedb_id' in entry:
            entry_id = int(entry['series_animedb_id'])
            result[entry_id] = {
                'id': entry_id,
                'title': entry['series_title'],
                'episode': int(entry['my_watched_episodes']),
                'status': int(entry['my_status']),
                'score': int(entry['my_score']),
                'total_episodes': int(entry['series_episodes']),
                'rewatching': int(entry['my_rewatching'] or 0),
                'status_name': STATUS_NAMES[int(entry['my_status'])],
            }
            # if was rewatching, so the status_name is rewatching
            if result[entry_id]['rewatching']:
                result[entry_id]['status_name'] = 'rewatching'


        # user stats
        if stats and 'user_id' in entry:
            result['stats'] = {}
            # copy entry dict to result['stats'] without all the 'user_'
            for k, v in entry.items():
                result['stats'][k.replace('user_', '')] = v

    return result

if os.path.isfile(save_path):
    with open(save_path, 'r') as f:
        my_list = json.load(f)

else:
    my_list = anime_list(username=username)

    for idd, info in tqdm(my_list.items()):
        anime = mal.get_anime(idd)
        anime.fetch()
        info['info'] = anime.info
        time.sleep(sleep)

    with open(save_path, 'w+') as f:
        json.dump(my_list, f)

pprint(my_list)
