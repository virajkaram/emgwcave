import argparse
from astropy.time import Time
from emgwcave.kowalski_utils import search_in_skymap, connect_kowalski, \
    default_projection_kwargs
from emgwcave.plotting import plot_skymap, save_thumbnails, make_full_pdf
from emgwcave.candidate_utils import save_candidates_to_file, \
    append_photometry_to_candidates, write_photometry_to_file
from emgwcave.fritz_filter import pythonised_fritz_emgw_filter_stage_1, \
    pythonised_fritz_emgw_filter_stationary_stage
import os
from emgwcave.skymap_utils import read_skymap_fits
from snipergw.model import EventConfig
from snipergw.skymap import Skymap
from emgwcave.paths import base_output_dir

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--event")
    parser.add_argument("-r", "--rev")
    parser.add_argument("-o", "--outputdir", default=base_output_dir)
    # parser.add_argument("skymappath", type=str)
    parser.add_argument("-cumprob", type=float, default=0.9)
    # parser.add_argument("outdir", type=str,
    #                     help='name of output directory for plots etc.')
    parser.add_argument("-start_date", type=str, default=None,
                        help='e.g. 2023-04-21T00:00:00')
    parser.add_argument("-end_date", type=str, help='2023-04-23T00:00:00', default=None)
    parser.add_argument("-instrument", type=str, choices=["ZTF", "WNTR"], default='ZTF')
    parser.add_argument("-filter", type=str, choices=['none', 'fritz'],
                        help='What filter do you want to use?', default='none'
                        )
    parser.add_argument("-customfilterfile", type=str,
                        help='File to use if using custom filter', default=None
                        )
    parser.add_argument("-nthreads", type=int, help="How many threads "
                                                    "to use on kowalski",
                        default=8)
    parser.add_argument("-plot_skymap", action="store_true")
    parser.add_argument("-plot_lightcurves_separately", action="store_true")
    parser.add_argument("-plot_thumbnails_separately", action="store_true")
    parser.add_argument("-mjd_event", type=float, default=None)

    args = parser.parse_args()

    event = EventConfig(**args.__dict__)
    skymap = Skymap(event)

    if args.start_date is None:
        start_date_jd = skymap.t_obs.jd
    else:
        start_date_jd = Time(args.start_date).jd

    if args.end_date is None:
        end_date_jd = start_date_jd + 5.
    else:
        end_date_jd = Time(args.end_date).jd

    # Set up paths and directories
    output_dir = args.outputdir

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
    filter_kwargs = {
        "candidate.drb": {"$gt": 0.3},
        "candidate.ndethist": {"$gt": 1},
    }

    # Set up Kowalski connection and run query
    kowalski = connect_kowalski()
    candidates = search_in_skymap(k=kowalski,
                                  skymap_path=skymap.skymap_path,
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
    if args.filter == 'fritz':
        selected_candidates = pythonised_fritz_emgw_filter_stage_1(
            selected_candidates)
    print(f"Filtered {len(selected_candidates)} alerts.")

    # Get full photometry history for the selected candidates
    selected_candidates = append_photometry_to_candidates(selected_candidates)

    if args.filter == 'fritz':
        selected_candidates = pythonised_fritz_emgw_filter_stationary_stage(
            selected_candidates)

    print(f"Filtered {len(selected_candidates)} alerts.")

    # TODO : Can get thumbnails separately for only the sources that passed to make
    #  the query faster

    # Make diagnostic plots
    ras = [x['candidate']['ra'] for x in selected_candidates]
    decs = [x['candidate']['dec'] for x in selected_candidates]
    if args.plot_skymap:
        plot_skymap(args.skymappath, flatten=True, ras=ras, decs=decs)

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
                  mjd0=skymap.t_obs.mjd,)

    # app.run(debug=True, port=8000)
