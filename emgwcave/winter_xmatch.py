from emgwcave.avro_utils import load_avro, load_avro_as_df
from emgwcave.kowalski_utils import connect_kowalski, get_cone_search_query
from emgwcave.candidate_utils import get_candidates_in_localization
from emgwcave.skymap_utils import get_mjd_from_skymap
from glob import glob
import argparse
import pandas as pd
import numpy as np


def xmatch_kowalski_df(cat: pd.DataFrame, k, jd_start: float = 0):
    crds_dict = {}
    for ind, row in cat.iterrows():
        crds_dict[ind] = [row['ra'], row['dec']]

    query = get_cone_search_query(coords_dict=crds_dict,
                                  projection={'_id': 0,
                                              'objectId': 1,
                                              'candidate.magpsf': 1,
                                              'candidate.jd': 1},
                                  filter={'candidate.jdstarthist': {'$gt': jd_start}},
                                  catalog='ZTF_alerts',
                                  cone_search_radius=2
                                  )

    results = k.query(query)
    result_data = results['default']['data']['ZTF_alerts']

    ztf_id = []
    ztf_num_dets = []
    ztf_mag_psfs = []
    for ind in crds_dict:
        ztf_mag_psfs.append([x['candidate']['magpsf'] for x in result_data[f'{ind}']])
        ztf_num_dets.append(len(result_data[f'{ind}']))
        ztf_names = [x['objectId'] for x in result_data[f'{ind}']]
        if len(ztf_names) == 0:
            ztf_name = ''
        else:
            ztf_name = ztf_names[0]
        ztf_id.append(ztf_name)

    cat['ZTF_ids'] = ztf_id
    cat['ZTF_ndets'] = ztf_num_dets
    # cat['ZTF_mag_psfs'] = ztf_mag_psfs
    return cat


def get_ztf_xmatch(winter_cands: pd.DataFrame, jd_start:float = 0):
    # connect to Kowalski
    k = connect_kowalski()

    xmatch_res = []
    # Query 1000 sources at a time
    xmatch_inds = np.arange(0, len(winter_cands), 1000)
    for xm_id in xmatch_inds:
        df = winter_cands.iloc[xm_id:xm_id + 1000]
        xmatch_res.append(xmatch_kowalski_df(df, k, jd_start=jd_start))

    xmatch_res = pd.concat(xmatch_res).reset_index(drop=True)
    return xmatch_res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('avro_dir', type=str,
                        help='Directory containing avro files')
    parser.add_argument('outdir', type=str,
                        help='Output directory')
    parser.add_argument('-skymap', type=str,
                        help='crossmatch to skymap?')
    parser.add_argument('-cumprob', type=float,
                        default=0.9,
                        help='Skymap cumulative probability ')
    args = parser.parse_args()

    avro_list = glob(f"{args.avro_dir}/*.avro")
    all_cands = []
    for avro_file in avro_list:
        all_cands.append(load_avro_as_df(avro_file))

    winter_cands = pd.concat(all_cands).reset_index(drop=True)

    all_candidates = []
    for avro_file in avro_list:
        all_candidates += load_avro(avro_file)

    print(f"Loaded {len(winter_cands)} candidates")
    if args.skymap is not None:
        skymap_path = args.skymap
        winter_cands = get_candidates_in_localization(candidates=all_candidates,
                                                      skymap_path=skymap_path,
                                                      cumulative_probability
                                                      =args.cumprob)
        print(f"Found {len(winter_cands)} candidates in skymap")
        skymap_mjd = get_mjd_from_skymap(skymap_path)
        skymap_jd = skymap_mjd + 2400000.5
    else:
        skymap_jd = 0

    # connect to Kowalski
    k = connect_kowalski()

    xmatch_res = get_ztf_xmatch(winter_cands, jd_start=skymap_jd)
    winter_match_ztf = xmatch_res[xmatch_res['ZTF_ndet'] > 0]

    print(f"Found {len(winter_match_ztf)} matches with ZTF")

    winter_match_ztf.to_csv(f"{args.outdir}/ztf_xmatches.csv", index=False)

