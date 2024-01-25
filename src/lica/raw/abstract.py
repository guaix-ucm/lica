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

# ---------------------
# Thrid-party libraries
# ---------------------

# -----------
# Own package
# -----------

from .constants import CHANNELS, LABELS
from .roi import Rect, NRect


class AbstractImageLoader:

    def __init__(self, path, v_roi=None, channels=None):
        self._path = path
        self._v_roi = NRect(0.0, 0.0, 1.0, 1.0) if v_roi is None else v_roi
        self._full_image = True if (v_roi.w == 1 and v_roi.h == 1) else False
        self._channels = CHANNELS if channels is None else channels
        self._shape = None
        self._roi = None
        self._metadata = dict()
         

    # -----------------------------
    # To be used in derived classes
    # -----------------------------

    def _check_channels(self, err_msg):
        if 'G' in self._channels:
            raise NotImplementedError(err_msg)

    def _trim(self, pixels):
        if not self._full_image:
            roi = self._roi
            y0 = roi.y0  
            y1 = roi.y1
            x0 = roi.x0 
            x1 = roi.x1
            pixels = pixels[y0:y1, x0:x1]  # Extract ROI 
        return pixels

    def _select_by_channels(self, initial_list):
        output_list = list()
        for ch in self._channels:
            if ch == 'G':
                # This assumes that initial list is a pixel array list
                aver_green = (initial_list[1] + initial_list[2]).astype(np.float32) / 2
                output_list.append(aver_green)
            else:
                i = CHANNELS.index(ch)
                output_list.append(initial_list[i])
        return np.stack(output_list)

    # ----------
    # Public API
    # ----------

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
        return self._shape

    def roi(self):
        return self._roi

    def cfa_pattern(self):
        '''Returns the Bayer pattern as RGGB, BGGR, GRBG, GBRG strings'''
        raise NotImplementedError

    def saturation_levels(self):
        raise NotImplementedError
       
    def black_levels(self):
       raise NotImplementedError

    def load(self):
        '''Load a stack of Bayer colour planes selected by the channels sequence'''
        raise NotImplementedError
        

    def statistics(self):
        '''In-place statistics calculation for RPi Zero'''
         raise NotImplementedError