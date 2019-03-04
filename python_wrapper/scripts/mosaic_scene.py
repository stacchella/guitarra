'''
This script reduces all data from scence in parallel.
'''

# --------------
# import modules
# --------------

import argparse
import os
import shutil
import glob
import numpy as np

from astropy.io import fits
from astropy.stats import biweight_location
import montage_wrapper as montage


# --------------
# read command line arguments
# --------------

parser = argparse.ArgumentParser()
parser.add_argument("--filter", type=str, help="filter")
parser.add_argument("--path_raw_data", type=str, help="path of data")
args = parser.parse_args()

filter_in = args.filter
path_slp_img = args.path_raw_data


# ------------
# get images and move to new folder
# ------------

list_img = glob.glob(path_slp_img + '*' + filter_in + '*.slp.fits')

try:
    shutil.rmtree(path_slp_img + filter_in)
except:
    print("Can't delete work tree; probably doesn't exist yet")

os.makedirs(path_slp_img + filter_in)

print 'moving data...'
for f in list_img:
    shutil.copy(f, path_slp_img + filter_in)

list_img = glob.glob(path_slp_img + filter_in + '/*.slp.fits')


# --------------
# flat-fielding
# --------------

num_img = len(list_img)
flat_mat = np.zeros((num_img, 2048, 2048))

for ii in range(num_img):
    hdul = fits.open(list_img[ii])
    flat_mat[ii] = hdul[0].data[0]/np.nansum(hdul[0].data[0])
    hdul.close()

flat_mat[np.isnan(flat_mat)] = 1.0
flat = biweight_location(flat_mat, axis=0)
flat = flat/np.nansum(flat)
print 'number of nan in flat =', np.sum(np.isnan(flat))

# save flat
hdu = fits.PrimaryHDU(flat)
hdul = fits.HDUList([hdu])
hdul.writeto(path_slp_img + filter_in + '/' + filter_in + '_flat.fits')

for ii in range(num_img):
    with fits.open(list_img[ii], mode='update') as hdul:
        hdul[0].data[0] = hdul[0].data[0]/flat
        hdul.flush()
        hdul.close()


# ----------------------------------
# create mosaic
# ----------------------------------

print 'starting with mosaic...'
montage.mosaic(path_slp_img + filter_in, path_slp_img + filter_in + '/mosaic', combine='median', background_match=True)

