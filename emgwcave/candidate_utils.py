from pathlib import Path
import pandas as pd
from emgwcave.kowalski_utils import query_aux_alerts, connect_kowalski, get_find_query
from emgwcave.skymap_utils import read_flattened_skymap, in_skymap, flatten_skymap, \
    get_flattened_skymap_path
import numpy as np
from copy import deepcopy
from typing import Optional
import os
from emgwcave.plotting import plot_photometry


def save_candidates_to_file(candidates: list[dict],
                            savefile: str | Path):
    # with open(savefile.replace('.csv', '.json'), 'wb') as f:
    #     json.dump(candidates, f)

    for candidate in candidates:
        if 'cutoutScience' in candidate:
            _ = candidate.pop('cutoutScience')
        if 'cutoutTemplate' in candidate:
            _ = candidate.pop('cutoutTemplate')
        if 'cutoutDifference' in candidate:
            _ = candidate.pop('cutoutDifference')

    candidate_df = pd.json_normalize(candidates)
    candidate_df.to_csv(savefile, index=False)


def append_photometry_to_candidates(candidates: list[dict]):
    projection = {'prv_candidates': 1}
    k = connect_kowalski()
    for candidate in candidates:
        name = candidate['objectId']
        prv_candidates = query_aux_alerts(k=k,
                                          name=name,
                                          projection=projection)

        candidate['prv_candidates'] = prv_candidates['prv_candidates']

    return candidates


def write_photometry_to_file(candidates: list[dict],
                             phot_dir: str | Path = None,
                             plot: bool = False):
    for candidate in candidates:
        name = candidate['objectId']
        photometry_df = make_photometry(candidate)

        lcfilename = os.path.join(phot_dir, f'lc_{name}.csv')
        photometry_df.to_csv(lcfilename)
        if plot:
            lcplotfilename = os.path.join(phot_dir, f'lc_{name}.png')

            plot_photometry(photometry_df, lcplotfilename)


def make_photometry(alert,
                    jd_start: Optional[float] = None,
                    instrument: str = 'ZTF'):
    """
    Make a de-duplicated pandas.DataFrame with photometry of alert['objectId']
    Modified from Kowalksi (https://github.com/dmitryduev/kowalski)

    :param alert: candidate dictionary
    :param jd_start: date from which to start photometry from
    """
    alert = deepcopy(alert)
    top_level = [
        "schemavsn",
        "publisher",
        "objectId",
        "candid",
        "candidate",
        "prv_candidates",
        "cutoutScience",
        "cutoutTemplate",
        "cutoutDifference",
    ]
    # alert["candidate"] = {}

    # (keys having value in 3.)
    delete = [key for key in alert.keys() if key not in top_level]

    # delete the key/s
    for key in delete:
        alert["candidate"][key] = alert[key]
        del alert[key]

    alert["candidate"] = [alert["candidate"]]
    df_candidate = pd.DataFrame(alert["candidate"], index=[0])

    df_prv_candidates = pd.DataFrame(alert["prv_candidates"])

    df_light_curve = pd.concat(
        [df_candidate, df_prv_candidates], ignore_index=True, sort=False
    )

    # note: WNTR (like PGIR) uses 2massj, which is not in sncosmo as of
    # 20210803, cspjs seems to be close/good enough as an approximation
    if instrument == "ZTF":
        ztf_filters = {1: "ztfg", 2: "ztfr", 3: "ztfi"}
        df_light_curve["filter"] = df_light_curve["fid"].apply(
            lambda x: ztf_filters[x]
        )
    elif instrument == "WNTR":
        # 20220818: added WNTR
        # 20220929: nir bandpasses have been added to sncosmo
        nir_filters = {0: "ps1::y", 1: "2massj", 2: "2massh", 3: "2massks"}
        df_light_curve["filter"] = df_light_curve["fid"].apply(
            lambda x: nir_filters[x]
        )

    df_light_curve["magsys"] = "ab"
    df_light_curve["mjd"] = df_light_curve["jd"] - 2400000.5

    df_light_curve["mjd"] = df_light_curve["mjd"].astype(np.float64)
    df_light_curve["magpsf"] = df_light_curve["magpsf"].astype(np.float32)
    df_light_curve["sigmapsf"] = df_light_curve["sigmapsf"].astype(np.float32)

    df_light_curve = (
        df_light_curve.drop_duplicates(subset=["mjd", "magpsf"])
        .reset_index(drop=True)
        .sort_values(by=["mjd"])
    )

    # filter out bad data:
    mask_good_diffmaglim = df_light_curve["diffmaglim"] > 0
    df_light_curve = df_light_curve.loc[mask_good_diffmaglim]

    # convert from mag to flux

    # step 1: calculate the coefficient that determines whether the
    # flux should be negative or positive
    coeff = df_light_curve["isdiffpos"].apply(
        lambda x: 1.0 if x in [True, 1, "y", "Y", "t", "1"] else -1.0
    )

    # step 2: calculate the flux normalized to an arbitrary AB zeropoint of
    # 23.9 (results in flux in uJy)
    df_light_curve["flux"] = coeff * 10 ** (
            -0.4 * (df_light_curve["magpsf"] - 23.9)
    )

    # step 3: separate detections from non detections
    detected = np.isfinite(df_light_curve["magpsf"])
    undetected = ~detected

    # step 4: calculate the flux error
    df_light_curve["fluxerr"] = None  # initialize the column

    # step 4a: calculate fluxerr for detections using sigmapsf
    df_light_curve.loc[detected, "fluxerr"] = np.abs(
        df_light_curve.loc[detected, "sigmapsf"]
        * df_light_curve.loc[detected, "flux"]
        * np.log(10)
        / 2.5
    )

    # step 4b: calculate fluxerr for non detections using diffmaglim
    df_light_curve.loc[undetected, "fluxerr"] = (
            10 ** (-0.4 * (df_light_curve.loc[undetected, "diffmaglim"] - 23.9)) / 5.0
    )  # as diffmaglim is the 5-sigma depth

    # step 5: set the zeropoint and magnitude system
    df_light_curve["zp"] = 23.9
    df_light_curve["zpsys"] = "ab"

    # only "new" photometry requested?
    if jd_start is not None:
        w_after_jd = df_light_curve["jd"] > jd_start
        df_light_curve = df_light_curve.loc[w_after_jd]

    return df_light_curve


def get_thumbnails(candidates: list[dict],
                   catalog='ZTF_alerts'):
    projection = {'cutoutScience': 1,
                  'cutoutTemplate': 1,
                  'cutoutDifference': 1
                  }
    k = connect_kowalski()

    for candidate in candidates:
        query = get_find_query(catalog=catalog,
                               filter={'objectId': candidate['objectId']},
                               projection=projection)
        response = k.query(query=query)

        if response['default']['status'] == 'success':
            candidate['cutoutScience'] = response['default']['data'][0]['cutoutScience']
            candidate['cutoutTemplate'] = \
                response['default']['data'][0]['cutoutTemplate']
            candidate['cutoutDifference'] = response['default']['data'][0][
                'cutoutDifference']
        else:
            print(f'Failed to get cutouts for {candidate["objectId"]}')
            candidate['cutoutScience'] = np.zeros((1, 1))
            candidate['cutoutTemplate'] = np.zeros((1, 1))
            candidate['cutoutDifference'] = np.zeros((1, 1))

    return candidates


def deduplicate_candidates(candidates: list[dict]):
    """Deduplicate candidates by objectId by keeping the one with the latest jd"""
    if not isinstance(candidates, np.ndarray):
        candidates = np.array(candidates)
    all_jds = np.array([x['candidate']['jd'] for x in candidates])

    sortinds = np.argsort(all_jds)
    candidates = candidates[sortinds[::-1]]
    all_objectids = np.array([x['objectId'] for x in candidates])
    unique_objectids, unique_indices = np.unique(all_objectids, return_index=True)

    return candidates[unique_indices]


def get_candidates_in_localization(candidates: list[dict],
                                   skymap_path: str,
                                   cumulative_probability: float = 0.9):
    if not isinstance(candidates, np.ndarray):
        candidates = np.array(candidates)

    ras = np.array([x['candidate']['ra'] for x in candidates])
    decs = np.array([x['candidate']['dec'] for x in candidates])
    # Read skymap, calculate top pixels
    try:
        (skymap_data, _, _, _), _ = read_flattened_skymap(skymap_path)
    except IndexError:
        flattened_filepath = get_flattened_skymap_path(skymap_path)
        if not os.path.exists(flattened_filepath):
            flatten_skymap(skymap_path, flattened_filepath)
        (skymap_data, _, _, _), _ = read_flattened_skymap(flattened_filepath)

    in_skymap_mask = in_skymap(skymap_prob=skymap_data,
                               ra_obj=ras,
                               dec_obj=decs,
                               probability=cumulative_probability)
    return candidates[in_skymap_mask]
