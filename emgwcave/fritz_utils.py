import time
import os
import requests
import numpy as np


def api(method, endpoint, data=None):
    fritz_token = os.getenv("FRITZ_TOKEN")
    if fritz_token is None:
        err = "Please specify fritz token using export FRITZ_TOKEN=<>"
        print(err)
        raise ValueError(err)
    headers = {'Authorization': f'token {fritz_token}'}
    response = requests.request(method, endpoint, params=data, headers=headers)
    return response


def query_candidates_fritz(startdate: str,  # e.g. = '2022-10-01',
                           enddate: str,  # e.g. = '2022-10-02',
                           localization_name: str,
                           localization_dateobs: str,
                           groupids: str = '48',
                           localizationCumprob: float = 0.9,
                           numperpage: int = 5,
                           ):
    data = {
        'savedStatus': 'all',
        'startDate': startdate,
        'endDate': enddate,
        'groupIDs': f'{groupids}',
        'numPerPage': numperpage,
        'localizationDateobs': localization_dateobs,
        'localizationCumprob': localizationCumprob,
        'localizationName': localization_name,
        'firstDetectionAfter': '2023-05-13 22:17:19',
        'lastDetectionBefore': '2023-05-20 22:17:19',
    }

    print(data)
    pagenum = 1
    query_finished = False
    candidate_list = []
    while not query_finished:
        data['pageNumber'] = pagenum
        response = api('GET', 'https://fritz.science/api/candidates', data=data)
        print(response.text)
        print(f'Queried page {pagenum}')
        pagenum += 1
        if response.status_code == 504:
            raise ValueError('Query timed out')
        if response.status_code == 400:
            query_finished = True
            continue
        candidate_list += response.json()['data']['candidates']
        time.sleep(2)

    return np.array(candidate_list)
