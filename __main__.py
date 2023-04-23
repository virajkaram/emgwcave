import argparse
from astropy.time import Time
from emgwcave.kowalski_utils import search_in_skymap, connect_kowalski, \
    default_projection_kwargs
from emgwcave.plotting import plot_skymap, save_thumbnails, make_full_pdf
from emgwcave.candidate_utils import save_candidates_to_file, get_photometry
from emgwcave.fritz_filter import fritz_emgw_filter
import os
import json
from emgwcave.skymap_utils import read_skymap_fits

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("skymappath", type=str)
    parser.add_argument("cumprob", type=float)
    parser.add_argument("end_date", type=str, help='2023-04-23T00:00:00')
    parser.add_argument("outdir", type=str, help='name of output directory')
    parser.add_argument("-start_date", type=str, default=None,
                        help='e.g. 2023-04-21T00:00:00')
    parser.add_argument("-instrument", type=str, choices=["ZTF", "WNTR"], default='ZTF')
    parser.add_argument("-filter", type=str, choices=['none', 'fritz', 'custom'],
                        help='What filter do you want to use?', default='none'
                        )
    parser.add_argument("-customfilterfile", type=str,
                        help='File to use if using custom filter', default=None
                        )
    parser.add_argument("-nthreads", type=int, help="How many threads "
                                                    "to use on kowalski",
                        default=8)
    parser.add_argument("-plot_skymap", action="store_true")
    parser.add_argument("-skip_thumbnail_plot", action="store_true")
    parser.add_argument("-skip_photometry_plot", action="store_true")
    parser.add_argument("-mjd_event", type=float, default=None)

    args = parser.parse_args()

    if args.mjd_event is None:
        try:
            _, _, _, _, header = read_skymap_fits(args.skymappath)
            mjd_event = header['MJD-OBS']
        except Exception as err:
            print("Error reading MJD-OBS, please provide it at commandline using"
                  " -mjdevent")
            raise err
    else:
        mjd_event = args.mjd_event

    if args.start_date is None:
        start_date_jd = mjd_event + 2400000.5
    else:
        start_date_jd = Time(args.start_date).jd
    end_date_jd = Time(args.end_date).jd

    # Set up paths and directories
    output_dir = args.outdir
    savefile = os.path.join(output_dir,
                            f"{args.instrument}_alerts_cumprob{args.cumprob}"
                            f"_{round(start_date_jd, 2)}_{end_date_jd}.csv")
    full_pdffile = os.path.join(output_dir,
                                f"{args.instrument}_alerts_cumprob{args.cumprob}"
                                f"_{round(start_date_jd, 2)}_{end_date_jd}.pdf")
    phot_dir = os.path.join(output_dir, 'photometry')
    thumbnails_dir = os.path.join(output_dir, 'thumbnails')
    for d in [phot_dir, thumbnails_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    # Get the filter to use
    if args.filter == 'none':
        filter_kwargs = {
            "candidate.drb": {"$gt": 0.7},
            "candidate.ndethist": {"$gt": 1},
        }

    elif args.filter == 'fritz':
        filter_kwargs = fritz_emgw_filter

    else:
        filter_kwargs = json.load(args.customfilterfile)

    # Set up Kowalski connection and run query
    kowalski = connect_kowalski()
    candidates = search_in_skymap(k=kowalski,
                                  skymap_path=args.skymappath,
                                  cumprob=args.cumprob,
                                  jd_start=start_date_jd,
                                  jd_end=end_date_jd,
                                  catalogs=['ZTF_alerts'],
                                  filter_kwargs=filter_kwargs,
                                  projection_kwargs=default_projection_kwargs,
                                  max_n_threads=args.nthreads
                                  )

    selected_candidates = candidates['default']['ZTF_alerts']
    print(f"Retrieved {len(selected_candidates)} alerts.")

    # Make diagnostic plots
    ras = [x['candidate']['ra'] for x in selected_candidates]
    decs = [x['candidate']['dec'] for x in selected_candidates]
    if args.plot_skymap:
        plot_skymap(args.skymappath, flatten=True, ras=ras, decs=decs)

    if not args.skip_thumbnail_plot:
        save_thumbnails(selected_candidates,
                        thumbnails_dir=thumbnails_dir)

    # Save candidate info to CSV file
    save_candidates_to_file(selected_candidates, savefile)

    if not args.skip_photometry_plot:
        get_photometry(selected_candidates, phot_dir=phot_dir)

    make_full_pdf(selected_candidates,
                  thumbnails_dir=thumbnails_dir,
                  phot_dir=phot_dir,
                  pdffilename=full_pdffile,
                  mjd0=mjd_event)

    # app.run(debug=True, port=8000)
