from penquins import Kowalski
import os
from pathlib import Path

default_projection_kwargs = {
    "candidate.jdstarthist": 1,
    "candidate.isdiffpos": 1,
    "candidate.drb": 1,
    "candidate.magpsf": 1,
    "candidate.jd": 1,
    "candidate.ssdistnr": 1,
    "candidate.ssmagnr": 1,
    "candidate.distpsnr1": 1,
    "candidate.sgscore1": 1,
    "candidate.distpsnr2": 1,
    "candidate.srmag2": 1,
    "candidate.sgscore2": 1,
    "candidate.distpsnr3": 1,
    "candidate.srmag3": 1,
    "candidate.sgscore3": 1,
    "candidate.sgmag1": 1,
    "candidate.srmag1": 1,
    "candidate.simag1": 1,
    "candidate.distnr": 1,
    "candidate.magnr": 1,
    "candidate.diffmaglim": 1,
    "candidate.fid": 1,
    "candidate.magap": 1,
    }


def connect_kowalski():
    kowalski_token = os.getenv('KOWALSKI_TOKEN')
    kowalski_url = os.getenv('KOWALSKI_URL')
    kowalski_port = os.getenv('KOWALSKI_PORT')

    if kowalski_token is None:
        err = "Please specify Kowalski token using export KOWALSKI_TOKEN=<>"
        print(err)
        raise ValueError(err)

    if kowalski_url is None:
        err = "Please specify Kowalski url using export KOWALSKI_URL=<>"
        print(err)
        raise ValueError(err)

    if kowalski_port is None:
        err = "Please specify Kowalski port using export KOWALSKI_PORT=<>"
        print(err)
        raise ValueError(err)

    protocol, host, port = "https", kowalski_url, kowalski_port
    kowalski = Kowalski(token=kowalski_token, protocol=protocol, host=host, port=port)
    connection_ok = kowalski.ping()
    print(f'Connection OK: {connection_ok}')
    return kowalski


def query_aux_alerts(k, name, projection=None, instrument="ZTF"):
    if projection is None:
        projection = {'prv_candidates': 0}

    # Run a find query on ZTF aux alerts catalog
    q = {
        'query_type': 'find',
        'query': {
            'catalog': f'{instrument}_alerts_aux',
            'filter': {
                '_id': name
            },
            'projection': projection,
        }
    }

    r = k.query(query=q)
    data = r['default']['data'][0]
    return data


def run_pipeline_offline(k, pipelines_array):
    queries = [{
        "query_type": "aggregate",
        "query": {
            "catalog": "ZTF_alerts",
            "pipeline": pipeline,
            "kwargs": {
                "max_time_ms": 100000
            }
        }
    } for pipeline in pipelines_array]

    # response = k.query(query=q)
    responses = k.batch_query(queries=queries, n_treads=len(pipelines_array))

    data = []
    for response in responses:
        print(f"Response {response['status']}:{response['message']}")
        data = data+response.get("data")

    return data


def search_in_skymap(k: Kowalski,
                     skymap_path: Path,
                     cumprob: float,
                     jd_start: float,
                     jd_end: float,
                     jdstarthist_start: float,
                     jdstarthist_end: float,
                     max_n_threads: int = 8,
                     catalogs: list = ['ZTF_alerts'],
                     filter_kwargs: dict = {},
                     projection_kwargs: dict = {}):
    cands_in_skymap = k.query_skymap(path=skymap_path,
                                     cumprob=cumprob,
                                     jd_start=jd_start,
                                     jd_end=jd_end,
                                     jdstarthist_start=jdstarthist_start,
                                     jdstarthist_end=jdstarthist_end,
                                     catalogs=catalogs,
                                     program_ids=[1, 2, 3],
                                     filter_kwargs=filter_kwargs,
                                     projection_kwargs=projection_kwargs,
                                     max_n_threads=max_n_threads
                                     )

    return cands_in_skymap


def get_find_query(catalog: str,
                   filter: dict,
                   projection: dict,
                   query_kwargs: dict = {}):
    q = {
        'query_type': 'find',
        'query': {
            'catalog': catalog,
            'filter': filter,
            'projection': projection,
            'kwargs': query_kwargs
        }
    }
    return q


def get_cone_search_query(coords_dict: dict,
                          catalog: str,
                          projection: dict,
                          filter: dict = {},
                          cone_search_radius: float = 2):
    query = {
        "query_type": "cone_search",
        "query": {
            "object_coordinates": {
                "cone_search_radius": cone_search_radius,
                "cone_search_unit": "arcsec",
                "radec": coords_dict,
            },
            "catalogs": {
                catalog: {
                    "filter": filter,
                    "projection": projection,
                }
            }
        },
        "kwargs": {
            "filter_first": False
        }
    }
    return query
