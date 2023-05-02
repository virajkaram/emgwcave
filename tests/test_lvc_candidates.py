"""
Test for ZTF in EMGWCave
"""

from emgwcave.__main__ import filter_candidates, setup_output_directories
import unittest
from emgwcave.skymap_utils import get_mjd_from_skymap
from astropy.time import Time

skymap_path = 'data/skymaps/2023-04-17T22-42-11_bayestar.multiorder.fits'
mjd_event = get_mjd_from_skymap(skymap_path=skymap_path)
start_date_jd = mjd_event + 2400000.5
end_date_jd = Time('2023-04-20T22:42:11').jd
outdir = 'data/output'

NUM_CANDIDATES = 2
CANDIDATE_NAMES = ['ZTF23aagpsii', 'ZTF23aagpuvg']


class TestLVCFiltering(unittest.TestCase):
    """Test filtering of candidates"""

    def test_filtering(self):
        """Test filtering"""
        setup_output_directories(outdir)
        selected_candidates = filter_candidates(skymap_path=skymap_path,
                                                cumprob=0.9,
                                                mjd_event=mjd_event,
                                                start_date_jd=start_date_jd,
                                                end_date_jd=end_date_jd,
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
