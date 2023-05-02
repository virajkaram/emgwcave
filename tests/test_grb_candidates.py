"""
Test for ZTF in EMGWCave
"""

from emgwcave.__main__ import filter_candidates, setup_output_directories
import unittest
from astropy.time import Time

skymap_path = 'data/skymaps/2023-04-30T07-47-19_crossmatch-9457-9455.fits.fits'
mjd_event = 60064.324525
start_date_jd = mjd_event + 2400000.5
time_window_days = 1.675
end_date_jd = start_date_jd + time_window_days
outdir = 'data/output'

NUM_CANDIDATES = 5
CANDIDATE_NAMES = ['ZTF23aagfzjt', 'ZTF23aaitoyy', 'ZTF23aaitpey', 'ZTF23aaitrmv',
                   'ZTF23aaitsom']


class TestGRBFiltering(unittest.TestCase):
    """Test filtering of candidates"""

    def test_filtering(self):
        """Test filtering"""
        setup_output_directories(outdir)
        selected_candidates = filter_candidates(skymap_path=skymap_path,
                                                cumprob=0.9,
                                                mjd_event=mjd_event,
                                                start_date_jd=start_date_jd,
                                                end_date_jd=end_date_jd,
                                                time_window_days=time_window_days,
                                                outdir=outdir,
                                                )
        self.assertEqual(len(selected_candidates), NUM_CANDIDATES)

        names = [candidate['objectId'] for candidate in selected_candidates]
        self.assertEqual(names, CANDIDATE_NAMES)


if __name__ == '__main__':
    setup_output_directories(outdir)
    selected_candidates = filter_candidates(skymap_path=skymap_path,
                                            cumprob=0.9,
                                            mjd_event=mjd_event,
                                            start_date_jd=start_date_jd,
                                            end_date_jd=end_date_jd,
                                            outdir=outdir,
                                            )
    print("Num candidates:", len(selected_candidates))
    print(f"Candidate "
          f"names: {[candidate['objectId'] for candidate in selected_candidates]}")
