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
from .roi import Roi, NormRoi
from .abstract import AbstractImageLoader

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

class FitsImageLoader(AbstractImageLoader):

    def __init__(self, path, v_roi, channels):
        super().__init__(path, v_roi, channels)
        self._fits()

    def get_header(self, header, tag, default=None):
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
                # Here we need to debayer, so a CFA keyword is needed
                self._cfa = self.get_header(header, 'BAYER')
                self._roi =  Roi.from_normalized_roi(width, height, self._n_roi, already_debayered=False)
                self._shape = (height //2, width //2)
            else:
                assert self._dim == 3
                Z = header['NAXIS3']
                height = header['NAXIS2']
                width =  header['NAXIS1']
                already_debayered = True
                self._roi =  Roi.from_normalized_roi(width, height, self._n_roi, already_debayered=True)
                self._shape = (height, width)
            # Generic metadata
            self._metadata['name'] = os.path.basename(self._path)
            self._metadata['roi'] = str(self._roi)
            self._metadata['channels'] = ' '.join(self._channels)
            self._metadata['exposure'] = header['EXPTIME']
            self._metadata['width'] = self._shape[1]
            self._metadata['height'] = self._shape[0]
            self._metadata['iso'] = self.get_header(header, 'ISO')
            self._metadata['camera'] = self.get_header(header,'CAMERA')
            self._metadata['maker'] = self.get_header(header,'MAKER')
            self._metadata['datetime'] = self.get_header(header,'DATE-OBS')
            self._metadata['focal_length'] = self.get_header(header,'FOCAL-LEN')
            self._metadata['f_number'] = self.get_header(header,'F-NUMBER')
        
     
    def _trim(self, pixels):
        '''Special case for 3D FITS'''
        if self._roi:
            y0 = self._roi.y0  
            y1 = self._roi.y1
            x0 = self._roi.x0 
            x1 = self._roi.x1
            pixels = pixels[:, y0:y1, x0:x1]  if self._dim == 3 else pixels[y0:y1, x0:x1]    
        return pixels

    def _load_cube(self):
        with fits.open(self._path) as hdul:
            pixels = hdul[0].data
            assert len(pixels.shape) == 3
            pixels = self._trim(pixels)
            if self._channels is None or len(self._channels) == 4:
                return pixels.copy()
            return self._select_by_channels(pixels)

    def _load_debayer(self):
        raise NotImplementedError

    def shape(self):
        '''Overrdies base method'''
        if self._dim == 2:
            return super().shape()
        else:
            return self._shape

    def load(self):
        ''' For the time being we only support FITS 3D cubes'''
        if self._dim == 2:
            nparray = self._load_debayer()
        else:
            nparray = self._load_cube()
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
