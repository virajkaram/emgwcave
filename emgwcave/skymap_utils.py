import healpy as hp
import numpy as np
from ligo.skymap.postprocess import find_greedy_credible_levels
from astropy.io import fits
from astropy.table import Table
from scipy.stats import norm
import os
from astropy.table import Column


def get_flattened_skymap_path(skymap_path):
    return skymap_path + '_flattened.fits'


def read_lvc_skymap_fits(filename):
    h = fits.open(filename)
    data = Table(h[1].data)

    prob = np.array(data['PROBDENSITY'])
    distmu = np.array(data['DISTMU'])
    distsigma = np.array(data['DISTSIGMA'])
    distnorm = np.array(data['DISTNORM'])

    header = h[1].header
    return prob, distmu, distsigma, distnorm, header


def read_fermi_skymap_fits(filename):
    h = fits.open(filename)
    data = Table(h[1].data)

    uniq = np.array(data['UNIQ'])
    prob = np.array(data['PROBDENSITY'])

    header = h[1].header
    return uniq, prob, header


def get_credible_levels(prob):
    npix = len(prob)
    credible_levels = find_greedy_credible_levels(prob)
    nside = hp.npix2nside(npix)
    return credible_levels


def dist_function(r, distnorm, distmu, distsigma):
    dp_dr = r ** 2 * distnorm * norm(distmu, distsigma).pdf(r)
    return dp_dr


def flatten_skymap(skymap_path, flatten_file_path, update_object_name=True):
    cmd = f'ligo-skymap-flatten {skymap_path} {flatten_file_path}'
    print(cmd)
    os.system(cmd)

    if update_object_name:
        h = fits.open(flatten_file_path, 'update')
        h[1].header['OBJECT'] = 'S' + str(h[1].header['OBJECT'])
        h.writeto(flatten_file_path, overwrite=True)


def read_flattened_skymap(flatten_file_path):

    (prob, distmu, distsigma, distnorm), hdr = hp.fitsfunc.read_map(flatten_file_path,
                                                                    verbose=False,
                                                                    partial=False,
                                                                    field=range(4),
                                                                    h=True)

    return (prob, distmu, distsigma, distnorm), hdr


def in_skymap(skymap_prob: np.ndarray,
              ra_obj: list,
              dec_obj: list,
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
