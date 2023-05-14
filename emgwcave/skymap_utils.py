import healpy as hp
import numpy as np
from ligo.skymap.postprocess import find_greedy_credible_levels
from astropy.io import fits
from scipy.stats import norm
import os
from astropy.table import Table
from astropy.time import Time


def get_flattened_skymap_path(skymap_path):
    return skymap_path + '_flattened.fits'


def read_lvc_skymap_fits(filename):
    h = fits.open(filename)
    data = Table(h[1].data)

    prob_density = np.array(data['PROBDENSITY'])
    distmu = np.array(data['DISTMU'])
    distsigma = np.array(data['DISTSIGMA'])
    distnorm = np.array(data['DISTNORM'])

    header = h[1].header
    return prob_density, distmu, distsigma, distnorm, header


def read_fermi_skymap_fits(filename):
    h = fits.open(filename)
    data = Table(h[1].data)
    uniq = np.array(data['UNIQ'])
    prob_density = np.array(data['PROBDENSITY'])
    # prob_density = np.array(data['PROBABILITY'])
    # prob_density = np.array(data['PROB'])
    header = h[1].header
    return uniq, prob_density, header


def get_credible_levels(prob):
    credible_levels = find_greedy_credible_levels(prob)
    return credible_levels


def dist_function(r, distnorm, distmu, distsigma):
    dp_dr = r ** 2 * distnorm * norm(distmu, distsigma).pdf(r)
    return dp_dr


def flatten_skymap(skymap_path, flatten_file_path, update_object_name=False):
    cmd = f'ligo-skymap-flatten {skymap_path} {flatten_file_path}'
    print(cmd)
    os.system(cmd)

    if update_object_name:
        h = fits.open(flatten_file_path, 'update')
        h[1].header['OBJECT'] = 'S' + str(h[1].header['OBJECT'])
        h.writeto(flatten_file_path, overwrite=True)


def read_flattened_skymap(flatten_file_path, num_fields=1):
    try:
        (prob, distmu, distsigma, distnorm), hdr = hp.fitsfunc. \
            read_map(flatten_file_path,
                     verbose=False,
                     partial=False,
                     field=4,
                     h=True)
    except IndexError:
        prob, hdr = hp.fitsfunc.read_map(flatten_file_path,
                                         verbose=False,
                                         partial=False,
                                         field=range(1),
                                         h=True)
        distmu, distsigma, distnorm = None, None, None

    return (prob, distmu, distsigma, distnorm), hdr


def in_skymap(skymap_prob: np.ndarray,
              ra_obj: list | np.ndarray,
              dec_obj: list | np.ndarray,
              probability: float = 0.9):
    # sortinds = np.argsort(skymap_prob)
    # skymap_prob = skymap_prob[sortinds]
    # cumprob = np.cumsum(skymap_prob)
    #
    # top_indices = sortinds[cumprob > 1 - probability]
    # pix = hp.ang2pix(nside, ra_obj, dec_obj, lonlat=True)
    # return pix in top_indices
    npix = len(skymap_prob)
    nside = hp.npix2nside(npix)
    ipix = hp.ang2pix(nside, ra_obj, dec_obj, lonlat=True)
    credible_levels = find_greedy_credible_levels(skymap_prob)
    return credible_levels[ipix] <= probability


def get_mjd_from_skymap(skymap_path):
    try:
        _, _, _, _, header = read_lvc_skymap_fits(skymap_path)
    except KeyError as err:
        print(f"Could not read skymap with LVC reader, trying with Fermi - {err}")
        try:
            _, _, header = read_fermi_skymap_fits(skymap_path)
        except KeyError as exc:
            print(f"Skymap could not be read by LVC or Fermi - {exc}")
            raise exc

    if 'MJD-OBS' in header:
        mjd_event = header['MJD-OBS']
    elif 'DATE-OBS' in header:
        mjd_event = Time(header['DATE-OBS']).mjd
    else:
        err = "Error reading MJD-OBS, please provide event date on " \
              "commandline using -date_event. e.g. 2023-04-04T22:30:00"
        raise KeyError(err)
    return mjd_event
