import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')
import healpy as hp
import pandas as pd

from emgwcave.skymap_utils import read_flattened_skymap, flatten_skymap
import numpy as np
from astropy.io import fits
import io
import gzip
from pathlib import Path
import os
from astropy.stats import sigma_clipped_stats
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages


def plot_skymap(mapfile, flatten=True, ras: list = None, decs: list = None):
    flattened_map_path = mapfile
    if flatten:
        flattened_map_path = mapfile + '_flattened.fits'
        flatten_skymap(skymap_path=mapfile,
                       flatten_file_path=flattened_map_path)

    fig = plt.figure()
    (prob, distmu, distsigma, distnorm), hdr = read_flattened_skymap(flattened_map_path)
    hp.mollview(prob, fig=fig, cmap='Oranges')

    if ras is not None:
        npix = len(prob)
        nside = hp.npix2nside(npix)

        sim_pixs = np.zeros(len(prob))
        thetas = 0.5 * np.pi - np.deg2rad(decs)
        phis = np.deg2rad(ras)
        ipixs = hp.ang2pix(nside=nside, theta=thetas, phi=phis)
        sim_pixs[ipixs] += 1

        hp.projscatter(thetas, phis, marker='x', s=0.001, color='black')

    plt.savefig(f"{mapfile}_mollweide.png",
                bbox_inches='tight')
    plt.close()


def get_data_from_bytes(iobyte):
    data = fits.open(io.BytesIO(gzip.open(io.BytesIO(iobyte), 'rb').read()))[0].data
    return data


def plot_thumbnail(data, savename=None, ax=None, save=True):
    if ax is None:
        plt.figure()
        ax = plt.gca()
    _, med, std = sigma_clipped_stats(data)
    ax.imshow(data, origin='lower', cmap='gray', vmax=med + 3 * std, vmin=med - 3 * std)
    if save:
        plt.savefig(savename)
        plt.close()
    return ax


def save_thumbnails(candidates: dict,
                    thumbnails_dir: str | Path):
    print(f'Saving thtumbnails to {thumbnails_dir}')
    for candidate in candidates:
        sci_cutout = candidate['cutoutScience']['stampData']
        ref_cutout = candidate['cutoutTemplate']['stampData']
        diff_cutout = candidate['cutoutDifference']['stampData']
        name = candidate['objectId']

        # print(name, sci_cutout)
        sci_cutout_data = get_data_from_bytes(sci_cutout)
        ref_cutout_data = get_data_from_bytes(ref_cutout)
        diff_cutout_data = get_data_from_bytes(diff_cutout)

        with open(os.path.join(thumbnails_dir, f"{name}_sci.npy"), 'w') as f:
            np.savetxt(f, sci_cutout_data)

        with open(os.path.join(thumbnails_dir, f"{name}_ref.npy"), 'w') as f:
            np.savetxt(f, ref_cutout_data)

        with open(os.path.join(thumbnails_dir, f"{name}_diff.npy"), 'w') as f:
            np.savetxt(f, diff_cutout_data)

        sci_thumbname = os.path.join(thumbnails_dir, f"{name}_sci.png")
        ref_thumbname = os.path.join(thumbnails_dir, f"{name}_ref.png")
        diff_thumbname = os.path.join(thumbnails_dir, f"{name}_diff.png")
        plot_thumbnail(sci_cutout_data, sci_thumbname)
        plot_thumbnail(ref_cutout_data, ref_thumbname)
        plot_thumbnail(diff_cutout_data, diff_thumbname)


color_dict = {'ztfg': 'green',
              'ztfr': 'red',
              'ztfi': 'orange',
              'ps1y': 'brown',
              '2massj': 'black',
              '2massh': 'red'
              }


def plot_photometry(photometry_df: pd.DataFrame,
                    savefile: str | Path = None,
                    save=True,
                    ax=None,
                    mjd0=0):
    if ax is None:
        plt.figure(figsize=(8, 6))
        ax = plt.gca()
    filts = np.unique(photometry_df['filter'])
    for filt in filts:
        df = photometry_df[photometry_df['filter'] == filt]
        detected = np.isfinite(df["magpsf"])
        undetected = ~detected
        ax.errorbar(df[detected]['mjd'] - mjd0, df[detected]['magpsf'],
                    yerr=df[detected]['sigmapsf'], color=color_dict[filt], fmt='.')

        ax.plot(df[undetected]['mjd'] - mjd0, df[undetected]['diffmaglim'], 'v',
                color=color_dict[filt], alpha=0.3)

    ax.invert_yaxis()

    if save:
        plt.savefig(savefile, bbox_inches='tight')
        plt.close()

    return ax


def make_full_pdf(selected_candidates: dict,
                  thumbnails_dir: str | Path,
                  phot_dir: str | Path,
                  pdffilename: str,
                  mjd0=0):
    with PdfPages(pdffilename) as pdf:
        for candidate in selected_candidates:
            fig = plt.figure()
            gs = GridSpec(nrows=2, ncols=3)

            name = candidate['objectId']

            try:
                sci_thumbnail_data = np.loadtxt(os.path.join(thumbnails_dir,
                                                             f"{name}_sci.npy"))
                ref_thumbnail_data = np.loadtxt(os.path.join(thumbnails_dir,
                                                             f"{name}_ref.npy"))
                diff_thumbnail_data = np.loadtxt(os.path.join(thumbnails_dir,
                                                              f"{name}_diff.npy"))

            except FileNotFoundError as err:
                print("Maybe the thumbnail plots were not created locally. Please run "
                      "without -skip_thumbnails option.")
                raise err

            photometry_df = pd.read_csv(os.path.join(phot_dir,
                                                     f"lc_{name}.csv"))

            ax = plt.subplot(gs[0])
            ax = plot_thumbnail(sci_thumbnail_data, ax=ax, save=False)
            ax.set_title('Sci')
            ax.set_xticks([])
            ax.set_yticks([])

            ax = plt.subplot(gs[1])
            ax = plot_thumbnail(ref_thumbnail_data, ax=ax, save=False)
            ax.set_title('Ref')
            ax.set_xticks([])
            ax.set_yticks([])

            ax = plt.subplot(gs[2])
            ax = plot_thumbnail(diff_thumbnail_data, ax=ax, save=False)
            ax.set_title('Diff')
            ax.set_xticks([])
            ax.set_yticks([])

            ax = plt.subplot(gs[3:5])
            ax = plot_photometry(photometry_df, ax=ax, save=False, mjd0=mjd0)
            ax.axvline(0, ymin=0, ymax=1, linestyle='--', color='black')

            ax = plt.subplot(gs[5])
            ax.set_xlim(0, 20)
            ax.set_ylim(0, 10)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(0, 8, name, size=14)
            ax.text(0, 6, f"RA= {candidate['candidate']['ra']}", size=12)
            ax.text(0, 5, f"Dec = {candidate['candidate']['dec']}", size=12)
            ax.axis('off')
            pdf.savefig(fig)
            plt.close()
