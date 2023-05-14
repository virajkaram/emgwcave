import numpy as np
from emgwcave.candidate_utils import save_candidates_to_file
from copy import deepcopy

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
        source['asteroid_flag'] = (0 <= candidate['ssdistnr'] < 10)  # & (
        # candidate['ssmagnr'] < 20) # TODO: Figure out why this was here
        source['point_underneath_flag'] = (0 <= candidate['distpsnr1'] < 2) & (
                candidate['sgscore1'] > 0.76)
        source['brightstar_flag'] = ((0 <= candidate['distpsnr1'] < 20) & (
                0 <= candidate['srmag1'] < 15) & (candidate['sgscore1'] > 0.49)) \
                                    | ((0 <= candidate['distpsnr2'] < 20) & (
                0 <= candidate['srmag2'] < 15) & (candidate['sgscore2'] > 0.49)) \
                                    | ((0 <= candidate['distpsnr3'] < 20) & (
                0 <= candidate['srmag3'] < 15) & (candidate['sgscore3'] > 0.49)) \
                                    | ((candidate['sgscore1'] == 0.5) & (
                0 <= candidate['distpsnr1'] < 0.5) & ((0 <= candidate['sgmag1'] < 17) | (
                0 <= candidate['srmag1'] < 17) | (0 <= candidate['simag1'] < 17)))

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


def pythonised_fritz_emgw_filter_stationary_stage(sources: list[dict],
                                                  mjd_event: float,
                                                  save: bool = True,
                                                  outdir: str = None):
    """
    The sources should now have the prv_candidates field. This function does a
    final filtering of the sources to remove non-stationary sources by looking at
    the difference between two consecutive detections
    :param outdir: output directory in which to write the data
    :param save: save a record of all the sources and the evaluated values
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
        if len(prv_candidate_jds) == 0:
            source['mindiff'] = 0
            source['earliest_detection'] = candidate['jd']
        else:
            source['mindiff'] = np.max(np.abs(prv_candidate_jds - candidate['jd']))
            source['earliest_detection'] = np.min(prv_candidate_jds)

        source['stationary_flag'] = np.any(
            (np.abs(prv_candidate_jds - candidate['jd']) > 0.01) &
            (prv_candidate_mags < 99) &
            prv_candidate_isdiffpos_flag
        )

        source['old_prv_cands_flag'] = source['earliest_detection'] > mjd_event \
                                       + 2400000.5

    if save:
        save_candidates_to_file(deepcopy(sources),
                                savefile=f'{outdir}/fritz_emgw_stationary_stage.csv')
    selected_source_mask = [(x['stationary_flag']) & (x['old_prv_cands_flag'])
                            for x in sources]

    return sources[selected_source_mask]
