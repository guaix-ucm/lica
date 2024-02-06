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

# ------------------------
# Own modules and packages
# ------------------------

from ..loader import ImageLoaderFactory, SimulatedDarkImage, NormRoi

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -------
# Classes
# -------

class ImageStatistics:
    def __init__(self, path, n_roi, channels, bias=None, dark=None):
        self._path = path
        self._n_roi = n_roi
        self._channels = channels
        self._factory =  ImageLoaderFactory()
        self._image = self._factory.image_from(path, n_roi, channels)
        self._pixels = None
        self._bias = None
        self._dark = None
        self._mean = None
        self._variance = None
        self._median = None
        self._configure(bias, dark)
    
    def _configure(self, bias, dark):
        if self._bias is not None:
            return
        N = len(self._channels)
        if bias is None:
            try:
                bias = self._image.black_levels()
                self._bias = np.array(self._image.black_levels()).reshape(N,1,1)
            except:
                log.warn("No luck using embedded image black levels as bias")
                self._bias =  np.full((N,1,1), 0)
        elif type(bias) == str:
            self._bias = self._factory.image_from(bias, self._n_roi, self._channels).load()
        elif type(bias) == float:
            self._bias =  np.full((N,1,1), bias)
        if dark is not None:
            self._dark = dark * self._image.exptime()
            log.info("Bias level per channel: %s. Dark count is %.02g", self._bias.reshape(-1), self._dark)
        else:
            log.info("Bias level per channel: %s.", self._bias.reshape(-1)) 

    def loader(self):
        '''access to underying image loader for extra methods such as image.exptime()'''
        return self._image

    def run(self):
        self._pixels = self._image.load().astype(dtype=np.float32, copy=False) - self._bias - self._dark # Stack of image color planes, cropped by ROI

    def name(self):
        return self._image.name()

    def pixels(self):
        return self._pixels

    def mean(self):
        if not self._mean:
            self._mean = np.mean(self._pixels,  axis=(1,2))
        return self._mean

    def variance(self):
        if not self._variance:
            self._variance = np.var(self._pixels, axis=(1,2), dtype=np.float64, ddof=1)
        return self._variance

    def std(self):
        if not self._variance:
            self._variance = np.var(self._pixels, axis=(1,2), dtype=np.float64, ddof=1)
        return np.sqrt(self._variance)

    def median(self):
        if not self._median:
            self._median = np.median(self._pixels,  axis=(1,2))
        return self._median



class ImagePairStatistics(ImageStatistics):
    '''Analize Image im pairs to remove Fixed Pattern Noise in the variance'''
    def __init__(self, path_a, path_b, n_roi, channels, bias=None):
        super().__init__(path_a, n_roi, channels, bias)
        self._path_b = path_b
        self._image_b = self._factory.image_from(path_b, n_roi, channels)
        self._diff = None
        self._pair_mean = None
        self._pair_variance = None

    def run(self):
        super().run()
        self._pixels_b = self._image_b.load().astype(np.float32, copy=False) - self._bias - self._dark

    def names(self):
        '''Like name() but returns'''
        return self._image.name(), self._image_b.name()

    def pair_mean(self):
        '''Mean of pair of images'''
        if not self._pair_mean:
            self._pair_mean = np.mean( (self._pixels + self._pixels_b),  axis=(1,2)) / 2
        return self._mean

    def adj_pair_variance(self):
        '''variance of pair adjusted by a final 1/2 factor'''
        if not self._pair_variance:
            self._pair_variance = np.var((self._pixels - self._pixels_b), axis=(1,2), dtype=np.float64, ddof=1) / 2
        return self._pair_variance

  