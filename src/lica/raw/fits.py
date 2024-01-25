# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import logging

# ---------------------
# Thrid-party libraries
# ---------------------

import numpy as np
from astropy.io import fits


# -----------
# Own package
# -----------

from .constants import CHANNELS, LABELS
from .roi import Rect


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

class FitsImage:

    def __init__(self, path):
        self._path = path
        self._metadata = dict()
        self._minimal_metadata()

    def _minimal_metadata(self):
        self._metadata['roi'] = None
        self._metadata['channels'] = None
        with fits.open(self._path) as hdul:
            header = hdul[0].header
            dim =  header['NAXIS']
            if dim == 2:
                height = header['NAXIS2']
                width =  header['NAXIS1']
                self._shape = (height, width)
            else:
                assert dim == 3
                Z = header['NAXIS3']
                height = header['NAXIS2']
                width =  header['NAXIS1']
                self._metadata['channels'] = tuple(header['CHANNELS'].split(' '))
                self._shape = (Z, height, width)
            self._metadata['name'] = os.path.basename(self._path)
            self._metadata['exposure'] = header['EXPTIME']
            self._metadata['width'] = width
            self._metadata['height'] = height
            self._metadata['camera'] = header['SENSOR']
            self._metadata['maker'] = header['MAKER']

    def _check_channels(self, channels, err_msg):
        channels = CHANNELS if channels is None else channels
        if 'G' in channels:
            raise NotImplementedError(err_msg)

    def _trim3d(self, pixels, roi):
        if roi:
            y0 = roi.y0  
            y1 = roi.y1
            x0 = roi.x0 
            x1 = roi.x1
            pixels = pixels[:, y0:y1, x0:x1]  # Extract ROI from cube
        return pixels

    def _load_cube(self, ro, channels):
        assert  self._metadata['channels'] == CHANNELS
        with fits.open(self._path) as hdul:
            pixels = hdul[0].data
            assert len(pixels.shape) == 3
            pixels = self._trim3d(pixels, roi)
            if channels is None or len(channels) == 4:
                return pixels.copy()
            output_list = list()
            for ch in channels:
                if ch == 'G':
                    # This assumes that initial list is a pixel array list
                    aver_green = (pixels[1] + pixels[2]) / 2
                    output_list.append(aver_green)
                else:
                    i = CHANNELS.index(ch)
                    output_list.append(pixels[i])
            return np.stack(output_list)

    def label(self, i):
        return LABELS[i]

    def metadata(self):
        return self._metadata

    def name(self):
        return self._metadata['name']

    def exposure(self):
        '''Useul for image list sorting by exposure time'''
        return self._metadata['exposure']

    def shape(self):
        return self._shape if len(self._shape) == 2 else tuple(self._shape[1:])

    def roi(self, n_x0=None, n_y0=None, n_width=1.0, n_heigth=1.0):
        if len (self._shape) == 3:
            width = self._shape[2]
            height = self._shape[1]
            debayered=True  # Misnomer, this means that we are not going to debayer ir
        else:
            width = self._shape[1]
            height = self._shape[0]
            debayered=False
        self._metadata['roi'] =  Rect.from_normalized(self._shape[1], self._shape[0], n_x0, n_y0, n_width, n_heigth, already_debayered=debayered)
        return self._metadata['roi']

    def cfa_pattern(self):
        '''Returns the Bayer pattern as RGGB, BGGR, GRBG, GBRG strings'''
        raise NotImplementeError("Not yet. Missing FITS keyword for this")

    def saturation_levels(self, channels=None):
        self._check_channels(channels, err_msg="saturation_levels on G=(Gr+Gb)/2 channel not available")
        raise NotImplementeError("Not yet. Missing FITS keyword for this")

    def black_levels(self, channels=None):
        self._check_channels(channels, err_msg="black_levels on G=(Gr+Gb)/2 channel not available")
        raise NotImplementeError("Not yet. Missing FITS keyword for this")

    def load(self, roi=None, channels=None):
        ''' For the time being we only support FITS 3D cubes'''
        nparray = self._load_cube(roi, channels)
        self._metadata['roi'] = self.roi() if roi is None else roi
        self._metadata['channels'] = CHANNELS if channels is None else channels
        return nparray

    def statistics(self, roi=None, channels=None):
        '''In-place statistics calculation for RPi Zero'''
        with fits.open(self._path) as hdul:
            pixels = hdul[0].data
            assert len(pixels.shape) == 3
            pixels = self._trim3d(pixels, roi)
            average = pixels.mean(axis=0)
            stdev = pixels.stdev(axis=0)
            self._metadata['roi'] = self.roi() if roi is None else roi
            self._metadata['channels'] = CHANNELS if channels is None else channels
            output_list = list()
            if channels is None or len(channels) == 4:
                 output_list = list(zip(average.tolist(), stdev.tolist()))
            else:
                for ch in channels:
                    if ch == 'G':
                        # This assumes that initial list is a pixel array list
                        aver_green = (average[1] + average[2]) /2
                        std_green = math.sqrt(stdev[1]**2 + stdev[2]**2)
                        output_list.append([aver_green, std_green])
                    else:
                        i = CHANNELS.index(ch)
                        output_list.append([average[i], stdev[i]])
                return np.stack(output_list)

    

    
# ------------------
# Auxiliary fnctions
# ------------------
