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
import fractions
import logging

# ---------------------
# Thrid-party libraries
# ---------------------

import rawpy
import exifread
import numpy as np

# -----------
# Own package
# -----------

from .constants import CHANNELS, LABELS
from .roi import Rect, NRect
from .abstract import ExifImageLoader


class SimulatedDarkImage(ExifImageLoader):

    def __init__(self, path,  roi=None, channels=None, dk_current=1.0, rd_noise=1.0):
        super().__init__(path, roi, channels)
        self._dk_current = dk_current
        self._rd_noise = rd_noise
        self._biases = (256, 256, 256, 256)

    def load(self):
        '''Get a stack of Bayer colour planes selected by the channels sequence'''
        self._check_channels(err_msg="In-place statistics on G=(Gr+Gb)/2 channel not available")
        raw_pixels_list = list()
        rng = np.random.default_rng()
        shape = (self._shape[0]//2, self._shape[1]//2)
        dark = [self._dk_current * self.exposure() for ch in CHANNELS]
        for i, ch in enumerate(CHANNELS):
            raw_pixels = self._biases[i] + dark[i]+ self._rd_noise * rng.standard_normal(size=shape)
            raw_pixels = np.asarray(raw_pixels, dtype=np.uint16)
            raw_pixels = self._trim(raw_pixels)
            raw_pixels_list.append(raw_pixels)
        return self._select_by_channels(raw_pixels_list)