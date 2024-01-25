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
from .roi import Rect, NRect
from .abstract import AbstractImageLoader

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

class FitsImageLoader(AbstractImageLoader):

    def __init__(self, path):
        super().__init__(path, roi, channels)
        self._fits()

    def get_header(header, tag, default=None):
        try:
            value = header[tag]
        except KeyError:
            value = default
        return value


    def _fits(self):
        with fits.open(self._path) as hdul:
            header = hdul[0].header
            self._dim =  header['NAXIS']
            if self._dim == 2:
                height = header['NAXIS2']
                width =  header['NAXIS1']
                self._shape = (height, width)
                # Here we need to debayer, so a CFA keyword is needed
                self._cfa = self.get_header(header, 'BAYER')
                already_debayered=False
            else:
                assert self._dim == 3
                Z = header['NAXIS3']
                height = header['NAXIS2']
                width =  header['NAXIS1']
                already_debayered = True
            # Generic metadata
            self._shape = (height, width)
            self._roi =  Rect.from_normalized(self._shape[1], self._shape[0], self._v_roi, already_debayered=already_debayered)
            self._metadata['name'] = os.path.basename(self._path)
            self._metadata['roi'] = str(self._roi)
            self._metadata['channels'] = ' '.join(self._channels)
            self._metadata['exposure'] = header['EXPTIME']
            self._metadata['width'] = width
            self._metadata['height'] = height
            self._metadata['iso'] = self.get_header(header, 'ISO')
            self._metadata['camera'] = self.get_header(header,'SENSOR')
            self._metadata['maker'] = self.get_header(header,'MAKER')
            self._metadata['datetime'] = self.get_header(header,'DATE-OBS')
            self._metadata['focal_length'] = self.get_header(header,'FOCAL-LEN')
            self._metadata['f_number'] = self.get_header(header,'F-NUMBER')
        
     
    def _trim(self, pixels):
        '''Special case for 3D FITS'''
        if self._roi:
            y0 = roi.y0  
            y1 = roi.y1
            x0 = roi.x0 
            x1 = roi.x1
            pixels = pixels[:, y0:y1, x0:x1]  if self._dim == 3 else pixels[y0:y1, x0:x1]    
        return pixels

    def _load_cube(self):
        with fits.open(self._path) as hdul:
            pixels = hdul[0].data
            assert len(pixels.shape) == 3
            pixels = self._trim(pixels)
            if channels is None or len(channels) == 4:
                return pixels.copy()
            return self._select_by_channels(pixels)

    def _load_debayer(self):
        raise NotImplementedError

    def load(self):
        ''' For the time being we only support FITS 3D cubes'''
        if self._dim == 2:
            nparray = self._load_debayer()
        else:
            nparray = self._load_cube(roi, channels)
        return nparray

    def statistics(self):
        '''In-place statistics calculation for RPi Zero'''
        with fits.open(self._path) as hdul:
            pixels = hdul[0].data
            assert len(pixels.shape) == 3
            pixels = self._trim(pixels)
            average = pixels.mean(axis=0)
            stdev = pixels.stdev(axis=0)
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
