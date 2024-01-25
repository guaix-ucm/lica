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

from . import CHANNELS, LABELS
from .roi import Rect


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

class FITSImage:

    def __init__(self, path):
        self._path = path
        self._metadata = dict()
        self._minimal_metadata()

    def _minimal_metadata(self):
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

    def _trim3d(self, pixels, roi):
        if roi:
            y0 = roi.y0  
            y1 = roi.y1
            x0 = roi.x0 
            x1 = roi.x1
            pixels = pixels[:, y0:y1, x0:x1]  # Extract ROI from cube
        return pixels

    def label(self, i):
        return LABELS[i]

    def name(self):
        return self._metadata['name']

    def metadata(self):
        return self._metadata

    def shape(self):
        return self._shape if len(self._shape) == 2 else tuple(self._shape[1:])

    def roi(self, n_x0=None, n_y0=None, n_width=1.0, n_heigth=1.0):
        if len (self._shape) == 3:
            width = self._shape[2]
            height = self._shape[1]
            debayered=False  # Misnomer, this means that we are not going to debayer ir
        else:
            width = self._shape[1]
            height = self._shape[0]
            debayered=True
        return Rect.from_normalized(width, height, n_x0, n_y0, n_width, n_heigth, debayered=debayered)

    def load_cube(self, roi=None, channels=None):
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
                    i = RawImage.CHANNELS.index(ch)
                    output_list.append(pixels[i])
            return np.stack(output_list)

    
# ------------------
# Auxiliary fnctions
# ------------------
