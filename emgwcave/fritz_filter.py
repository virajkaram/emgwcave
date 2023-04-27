import numpy as np

fritz_emgw_filter = {}


def pythonised_fritz_emgw_filter_stage_1(sources: list[dict]):
    """Filter candidates using the Fritz EMGW filter, but in python instead of mongo
    """
    if not isinstance(sources, np.ndarray):
        sources = np.array(sources)

    for source in sources:
        candidate = source['candidate']
        candidate['age'] = candidate['jd'] - candidate['jdstarthist']

        source['positive_sub_flag'] = candidate['isdiffpos'] in ['t', '1', 'True', True,
                                                                 1]
        source['real_flag'] = candidate['drb'] > 0.3
        source['young_flag'] = candidate['jd'] - candidate['jdstarthist'] < 10
        source['asteroid_flag'] = (0 < candidate['ssdistnr'] < 10) & (
                candidate['ssmagnr'] < 20)
        source['point_underneath_flag'] = (candidate['distpsnr1'] < 2) & (
                                                         candidate['sgscore1'] > 0.76)
        source['brightstar_flag'] = ((0 < candidate['distpsnr1'] < 20) & (
                0 < candidate['srmag1'] < 15) & (candidate['sgscore1'] > 0.49)) \
                                    | ((0 < candidate['distpsnr2'] < 20) & (
                0 < candidate['srmag2'] < 15) & (candidate['sgscore2'] > 0.49)) \
                                    | ((0 < candidate['distpsnr3'] < 20) & (
                0 < candidate['srmag3'] < 15) & (candidate['sgscore3'] > 0.49)) \
                                    | ((candidate['sgscore1'] == 0.5) & (
                0 < candidate['distpsnr1'] < 0.5) & ((0 < candidate['sgmag1'] < 17) | (
                0 < candidate['srmag1'] < 17) | (0 < candidate['simag1'] < 17)))

        source['variable_source_flag'] = ((0 < candidate['distnr'] < 0.4) & (
                candidate['magnr'] < 19) & (candidate['age'] > 90)) \
                                         | ((0 < candidate['distnr'] < 0.8) & (
                0 < candidate['magnr'] < 17) & (candidate['age'] > 90)) \
                                         | ((0 < candidate['distnr'] < 1.2) & (
                0 < candidate['magnr'] < 16) & (candidate['age'] > 90))

        source['fritz_emgw_filter_1_flag'] = source['positive_sub_flag'] \
                                             & source['real_flag'] \
                                             & source['young_flag'] \
                                             & ~source['asteroid_flag'] \
                                             & ~source['point_underneath_flag'] \
                                             & ~source['brightstar_flag'] \
                                             & ~source['variable_source_flag']
    selected_source_mask = np.array([x['fritz_emgw_filter_1_flag']
                                     for x in sources]).astype(bool)
    return sources[selected_source_mask]


def pythonised_fritz_emgw_filter_stationary_stage(sources: list[dict]):
    """
    The sources should now have the prv_candidates field. This function does a
    final filtering of the sources to remove non-stationary sources by looking at
    the difference between two consecutive detections
    :param sources:
    :return:
    """
    if not isinstance(sources, np.ndarray):
        sources = np.array(sources)

    for source in sources:
        candidate = source['candidate']
        prv_candidates = source['prv_candidates']
        prv_candidates_detections = [x for x in prv_candidates if 'magpsf' in x.keys()]
        prv_candidate_jds = np.array([x['jd'] for x in prv_candidates_detections])
        prv_candidate_mags = np.array([x['magpsf'] for x in prv_candidates_detections])
        prv_candidate_isdiffpos_flag = np.array([x['isdiffpos'] in ['1', 1, 't', True]
                                                 for x in
                                                 prv_candidates_detections]).astype(
            bool)

        source['stationary_flag'] = np.any(
            (np.abs(prv_candidate_jds - candidate['jd']) > 0.02) &
            (prv_candidate_mags < 99) &
            prv_candidate_isdiffpos_flag
        )

    selected_source_mask = [x['stationary_flag'] for x in sources]

    # print([x['positive_sub_flag'] for x in sources[selected_source_mask]])
    # print([x['real_flag'] for x in sources[selected_source_mask]])
    # print([x['young_flag'] for x in sources[selected_source_mask]])
    # print([x['candidate']['jd'] for x in sources[selected_source_mask]])
    # print([x['candidate']['jdstarthist'] for x in sources[selected_source_mask]])
    # print([x['objectId'] for x in sources[selected_source_mask]])
    # print([x['asteroid_flag'] for x in sources[selected_source_mask]])
    # print([x['point_underneath_flag'] for x in sources[selected_source_mask]])
    # print([x['brightstar_flag'] for x in sources[selected_source_mask]])
    # print([x['variable_source_flag'] for x in sources[selected_source_mask]])
    # print([x['fritz_emgw_filter_1_flag'] for x in sources[selected_source_mask]])
    return sources[selected_source_mask]


# TODO Where is ndets >=2 implemented
var = [
    {
        "$project": {
            "_id": 1,
            "candid": 1,
            "objectId": 1,
            "prv_candidates.jd": 1,
            "prv_candidates.magpsf": 1,
            "prv_candidates.fid": 1,
            "prv_candidates.isdiffpos": 1,
            "prv_candidates.diffmaglim": 1,
            "isdiffpos": "$candidate.isdiffpos",
            "m_now": "$candidate.magpsf",
            "m_app": "$candidate.magap",
            "t_now": "$candidate.jd",
            "fid_now": "$candidate.fid",
            "sgscore": "$candidate.sgscore1",
            "sgscore2": "$candidate.sgscore2",
            "sgscore3": "$candidate.sgscore3",
            "srmag": "$candidate.srmag1",
            "srmag2": "$candidate.srmag2",
            "srmag3": "$candidate.srmag3",
            "sgmag": "$candidate.sgmag1",
            "simag": "$candidate.simag1",
            "rbscore": "$candidate.rb",
            "drbscore": "$candidate.drb",
            "magnr": "$candidate.magnr",
            "distnr": "$candidate.distnr",
            "distpsnr1": "$candidate.distpsnr1",
            "distpsnr2": "$candidate.distpsnr2",
            "distpsnr3": "$candidate.distpsnr3",
            "scorr": "$candidate.scorr",
            "fwhm": "$candidate.fwhm",
            "elong": "$candidate.elong",
            "nbad": "$candidate.nbad",
            "chipsf": "$candidate.chipsf",
            "gal_lat": "$coordinates.b",
            "ssdistnr": "$candidate.ssdistnr",
            "ssmagnr": "$candidate.ssmagnr",
            "ssnamenr": "$candidate.ssnamenr",
            "t_start": "$candidate.jdstarthist",
            "age": {
                "$subtract": [
                    "$candidate.jd",
                    "$candidate.jdstarthist"
                ]
            },
            "psfminap": {
                "$subtract": [
                    "$candidate.magpsf",
                    "$candidate.magap"
                ]
            }
        }
    },
    {
        "$project": {
            "objectId": 1,
            "t_now": 1,
            "t_start": 1,
            "m_now": 1,
            "fid_now": 1,
            "sgscore": 1,
            "rbscore": 1,
            "drbscore": 1,
            "magnr": 1,
            "distnr": 1,
            "scorr": 1,
            "gal_lat": 1,
            "ssdistnr": 1,
            "ssnamenr": 1,
            "ssmagnr": 1,
            "age": 1,
            "nbad": 1,
            "fwhm": 1,
            "elong": 1,
            "psfminap": 1,
            "prv_candidates": 1,
            "latitude": {
                "$gte": [
                    {
                        "$abs": "$gal_lat"
                    },
                    4
                ]
            },
            "positivesubtraction": {
                "$in": [
                    "$isdiffpos",
                    [
                        1,
                        "1",
                        "t",
                        True
                    ]
                ]
            },
            "real": {
                "$gt": [
                    "$drbscore",
                    0.3
                ]
            },
            "rock": {
                "$and": [
                    {
                        "$gte": [
                            "$ssdistnr",
                            0
                        ]
                    },
                    {
                        "$lt": [
                            "$ssdistnr",
                            10
                        ]
                    },
                    {
                        "$lt": [
                            {
                                "$abs": "$ssmagnr"
                            },
                            20
                        ]
                    }
                ]
            },
            "young": {
                "$lt": [
                    "$age",
                    10
                ]
            },
            "pointunderneath": {
                "$and": [
                    {
                        "$gt": [
                            "$sgscore",
                            0.76
                        ]
                    },
                    {
                        "$lt": [
                            "$distpsnr1",
                            2
                        ]
                    }
                ]
            },
            "brightstar": {
                "$or": [
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distpsnr1",
                                    20
                                ]
                            },
                            {
                                "$lt": [
                                    "$srmag",
                                    15
                                ]
                            },
                            {
                                "$gt": [
                                    "$srmag",
                                    0
                                ]
                            },
                            {
                                "$gt": [
                                    "$sgscore",
                                    0.49
                                ]
                            }
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distpsnr2",
                                    20
                                ]
                            },
                            {
                                "$lt": [
                                    "$srmag2",
                                    15
                                ]
                            },
                            {
                                "$gt": [
                                    "$srmag2",
                                    0
                                ]
                            },
                            {
                                "$gt": [
                                    "$sgscore2",
                                    0.49
                                ]
                            }
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distpsnr3",
                                    20
                                ]
                            },
                            {
                                "$lt": [
                                    "$srmag3",
                                    15
                                ]
                            },
                            {
                                "$gt": [
                                    "$srmag3",
                                    0
                                ]
                            },
                            {
                                "$gt": [
                                    "$sgscore3",
                                    0.49
                                ]
                            }
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$eq": [
                                    "$sgscore",
                                    0.5
                                ]
                            },
                            {
                                "$lt": [
                                    "$distpsnr1",
                                    0.5
                                ]
                            },
                            {
                                "$or": [
                                    {
                                        "$lt": [
                                            "$sgmag",
                                            17
                                        ]
                                    },
                                    {
                                        "$lt": [
                                            "$srmag",
                                            17
                                        ]
                                    },
                                    {
                                        "$lt": [
                                            "$simag",
                                            17
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "variablesource": {
                "$or": [
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distnr",
                                    0.4
                                ]
                            },
                            {
                                "$lt": [
                                    "$magnr",
                                    19
                                ]
                            },
                            {
                                "$gt": [
                                    "$age",
                                    90
                                ]
                            }
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distnr",
                                    0.8
                                ]
                            },
                            {
                                "$lt": [
                                    "$magnr",
                                    17
                                ]
                            },
                            {
                                "$gt": [
                                    "$age",
                                    90
                                ]
                            }
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$lt": [
                                    "$distnr",
                                    1.2
                                ]
                            },
                            {
                                "$lt": [
                                    "$magnr",
                                    15
                                ]
                            },
                            {
                                "$gt": [
                                    "$age",
                                    90
                                ]
                            }
                        ]
                    }
                ]
            },
            "stationary": {
                "$anyElementTrue": {
                    "$map": {
                        "input": "$prv_candidates",
                        "as": "cand",
                        "in": {
                            "$and": [
                                {
                                    "$gt": [
                                        {
                                            "$abs": {
                                                "$subtract": [
                                                    "$t_now",
                                                    "$$cand.jd"
                                                ]
                                            }
                                        },
                                        0.02
                                    ]
                                },
                                {
                                    "$lt": [
                                        "$$cand.magpsf",
                                        99
                                    ]
                                },
                                {
                                    "$in": [
                                        "$$cand.isdiffpos",
                                        [
                                            1,
                                            "1",
                                            True,
                                            "t"
                                        ]
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
    },
    {
        "$match": {
            "brightstar": False,
            "pointunderneath": False,
            "positivesubtraction": True,
            "real": True,
            "stationary": True,
            "variablesource": False,
            "young": True
        }
    },
]
