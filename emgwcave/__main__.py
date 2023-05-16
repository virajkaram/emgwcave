import argparse

import pandas as pd
from astropy.time import Time
from emgwcave.kowalski_utils import search_in_skymap, connect_kowalski, \
    default_projection_kwargs
from emgwcave.plotting import plot_skymap, save_thumbnails, make_full_pdf
from emgwcave.candidate_utils import save_candidates_to_file, \
    append_photometry_to_candidates, write_photometry_to_file, get_thumbnails, \
    deduplicate_candidates, get_candidates_in_localization, \
    get_candidates_crossmatch, annotate_candidates
from emgwcave.fritz_filter import pythonised_fritz_emgw_filter_stage_1, \
    pythonised_fritz_emgw_filter_stationary_stage
import os
from emgwcave.skymap_utils import get_mjd_from_skymap
from copy import deepcopy
from pathlib import Path
from emgwcave.fritz_utils import query_candidates_fritz
import numpy as np


def setup_output_directories(output_dir: str):
    phot_dir = os.path.join(output_dir, 'photometry')
    thumbnails_dir = os.path.join(output_dir, 'thumbnails')
    for d in [phot_dir, thumbnails_dir]:
        if not os.path.exists(d):
            Path(d).mkdir(parents=True, exist_ok=True)

    return phot_dir, thumbnails_dir


def filter_candidates(skymap_path: str | Path,
                      cumprob: float,
                      start_date_jd: float,
                      end_date_jd: float,
                      mjd_event: float,
                      time_window_days: float,
                      filter: str = 'fritz',
                      instrument: str = 'ZTF',
                      outdir='emgwcave_output',
                      nthreads: int = 8,
                      min_ndethist: int = 1,
                      localization_compare_skymappath: str | Path = None):
    # TODO: use different dates for jd and jdstarthist, as jdstarthist is
    #  3-sigma detections. So the default should be search for all alerts generated in
    #  the given time windo (i.e. now), but filter through only those that have
    #  jdstarthist within the first 3 or 5 days since the event. This will give all
    #  alerts that were first detected (albeit subthreshold) within the first 3 or
    #  5 days. Also sorts the problem of getting the latest photometry point. Actually
    #  the filter requires jd -jdstarthist < 10 days, so maybe we can use that
    #  instead of arbitrarily large days.

    jd_event = mjd_event + 2400000.5
    # Set up Kowalski connection and run query
    kowalski = connect_kowalski()
    candidates = search_in_skymap(k=kowalski,
                                  skymap_path=skymap_path,
                                  cumprob=cumprob,
                                  jd_start=start_date_jd,
                                  jd_end=end_date_jd,
                                  jdstarthist_start=jd_event,
                                  jdstarthist_end=jd_event + time_window_days,
                                  catalogs=[f'{instrument}_alerts'],
                                  projection_kwargs=default_projection_kwargs,
                                  max_n_threads=nthreads,
                                  filter_kwargs={"candidate.ndethist":
                                                     {"$gt": min_ndethist}}
                                  )

    selected_candidates = candidates['default'][f'{instrument}_alerts']
    print(f"Retrieved {len(selected_candidates)} alerts.")

    # Deduplicate candidates
    selected_candidates = deduplicate_candidates(selected_candidates)
    print(f"Retained {len(selected_candidates)} alerts after deduplication.")

    save_candidates_to_file(deepcopy(selected_candidates),
                            savefile=f'{outdir}/all_retrieved_alerts.csv')

    if localization_compare_skymappath is None:
        localization_compare_skymappath = skymap_path
    # Perform a second check for candidates in the skymap
    selected_candidates = get_candidates_in_localization(selected_candidates,
                                                         localization_compare_skymappath,
                                                         cumprob)
    print(f"Retained {len(selected_candidates)} alerts after localization check.")
    save_candidates_to_file(deepcopy(selected_candidates),
                            savefile=f'{outdir}/alerts_inside_localization.csv')

    if filter == 'fritz':
        selected_candidates = pythonised_fritz_emgw_filter_stage_1(
            selected_candidates, save=True, outdir=outdir)
    print(f"Filtered {len(selected_candidates)} alerts.")

    # Get full photometry history for the selected candidates
    selected_candidates = append_photometry_to_candidates(selected_candidates)

    if filter == 'fritz':
        selected_candidates = pythonised_fritz_emgw_filter_stationary_stage(
            selected_candidates, mjd_event=mjd_event,
            save=True, outdir=outdir)

    print(f"Filtered {len(selected_candidates)} alerts.")

    selected_candidates = get_candidates_crossmatch(selected_candidates)
    selected_candidates = annotate_candidates(selected_candidates)
    return selected_candidates


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("skymappath", type=str)
    parser.add_argument("cumprob", type=float)
    parser.add_argument("outdir", type=str,
                        help='name of output directory for plots etc.')
    parser.add_argument('-time_window_days', type=float, default=5.0,
                        help="Search for candidates that were first "
                             "detected within these many days since the event")
    parser.add_argument("-end_date", type=str,
                        help='Search for candidates detected '
                             'before this day, e.g. 2023-04-23T00:00:00 '
                             'default = event_day + time_window + 10 days '
                             '(10 days = age constraint in filter) ',
                        default=None
                        )
    parser.add_argument("-additional_skymappath", type=str,
                        help='If you want, you can pass the path to a separate '
                             'skymap that will be used to check whether '
                             'candidate is in localization. This is useful if the map '
                             'you use for kowalski queries is a fake-map generated '
                             'using crossmatch, because the skymap was not being '
                             'parsed', default=None)
    parser.add_argument("-start_date", type=str, default=None,
                        help='e.g. 2023-04-21T00:00:00')
    parser.add_argument("-instrument", type=str, choices=["ZTF", "WNTR"], default='ZTF')
    parser.add_argument("-min_ndethist", type=int, default=1)
    parser.add_argument("-filter", type=str, choices=['none', 'fritz'],
                        help='What filter do you want to use?', default='fritz'
                        )
    parser.add_argument("-nthreads", type=int, help="How many threads "
                                                    "to use on kowalski",
                        default=8)
    parser.add_argument("-plot_skymap", action="store_true")
    parser.add_argument("-plot_lightcurves_separately", action="store_true")
    parser.add_argument("-plot_thumbnails_separately", action="store_true")
    parser.add_argument("-date_event", type=str, default=None,
                        help="e.g. 2023-04-22T00:00:00")
    parser.add_argument("-do_fritz_comparison", action="store_true")
    parser.add_argument("-localization_name", type=str, default=None,
                        help="e.g. glg_healpix_..fit")
    parser.add_argument("-groupids", type=str, default='48',
                        help="Group ID on fritz, e.g. 48,49")

    args = parser.parse_args()

    skymap_path = args.skymappath
    if args.date_event is None:
        mjd_event = get_mjd_from_skymap(skymap_path)
    else:
        mjd_event = Time(args.date_event).mjd

    if args.start_date is None:
        start_date_jd = mjd_event + 2400000.5
    else:
        start_date_jd = Time(args.start_date).jd

    time_window_days = args.time_window_days

    if args.end_date is None:
        end_date_jd = mjd_event + 2400000.5 + time_window_days + 10
    else:
        end_date_jd = Time(args.end_date).jd

    localization_compare_skymappath = args.additional_skymappath
    if localization_compare_skymappath is None:
        localization_compare_skymappath = skymap_path
    # Set up paths and directories
    output_dir = args.outdir

    savefile = os.path.join(output_dir,
                            f"{os.path.basename(skymap_path).split('.fits')[0]}"
                            f"_{args.instrument}_alerts_cumprob{args.cumprob}"
                            f"_{round(start_date_jd, 2)}_{round(end_date_jd, 2)}"
                            f".csv")

    full_pdffile = savefile.replace(".csv", ".pdf")

    phot_dir, thumbnails_dir = setup_output_directories(output_dir)

    selected_candidates = filter_candidates(skymap_path=args.skymappath,
                                            cumprob=args.cumprob,
                                            time_window_days=args.time_window_days,
                                            instrument=args.instrument,
                                            min_ndethist=args.min_ndethist,
                                            mjd_event=mjd_event,
                                            filter=args.filter,
                                            start_date_jd=start_date_jd,
                                            end_date_jd=end_date_jd,
                                            nthreads=args.nthreads,
                                            outdir=output_dir,
                                            localization_compare_skymappath=localization_compare_skymappath,
                                            )

    # Get thumbnails
    selected_candidates = get_thumbnails(selected_candidates)

    # Make diagnostic plots
    ras = [x['candidate']['ra'] for x in selected_candidates]
    decs = [x['candidate']['dec'] for x in selected_candidates]
    if args.plot_skymap:
        plot_skymap(skymap_path, output_dir, flatten=True, ras=ras, decs=decs)

    save_thumbnails(selected_candidates,
                    thumbnails_dir=thumbnails_dir,
                    plot=args.plot_thumbnails_separately)

    # Save candidate info to CSV file
    save_candidates_to_file(selected_candidates, savefile)

    write_photometry_to_file(selected_candidates,
                             phot_dir=phot_dir,
                             plot=args.plot_lightcurves_separately)

    make_full_pdf(selected_candidates,
                  thumbnails_dir=thumbnails_dir,
                  phot_dir=phot_dir,
                  pdffilename=full_pdffile,
                  mjd0=mjd_event)

    if args.do_fritz_comparison:
        if args.localization_name is None:
            raise ValueError("Please provide localization name with -localization_name")
        start_date_str = Time(start_date_jd, format='jd').iso.split(' ')[0]
        end_date_str = Time(end_date_jd, format='jd').iso.split(' ')[0]
        localization_dateobs = Time(mjd_event, format='mjd').isot
        fritz_candidates = query_candidates_fritz(startdate=start_date_str,
                                                  enddate=end_date_str,
                                                  localization_name=args.localization_name,
                                                  localization_dateobs=localization_dateobs,
                                                  localizationCumprob=args.cumprob,
                                                  groupids=args.groupids
                                                  )
        fritz_candidate_ztf_names = np.array([x['id'] for x in fritz_candidates])

        np.savetxt(os.path.join(output_dir, 'fritz_candidates.txt'),
                   fritz_candidate_ztf_names, fmt='%s')

        cave_candidates = pd.read_csv(savefile)
        cave_candidate_ztf_names = np.array(cave_candidates['objectId'])
        print(f"Found {len(cave_candidate_ztf_names)} candidates in CAVE")
        print(f"Found {len(fritz_candidate_ztf_names)} candidates in Fritz")
        missing_cave_candidates = np.setdiff1d(fritz_candidate_ztf_names,
                                               cave_candidate_ztf_names)
        print(f"Candidates in Fritz but not in CAVE : {missing_cave_candidates}")
        missing_fritz_candidates = np.setdiff1d(cave_candidate_ztf_names,
                                                fritz_candidate_ztf_names)
        print(f"Candidates in CAVE but not in Fritz : {missing_fritz_candidates}")
