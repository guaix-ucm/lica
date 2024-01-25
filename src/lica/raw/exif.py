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
from .abstract import AbstractImageLoader

# ---------
# Constants
# ---------


# ----------
# Exceptions
# ----------

class UnsupportedCFAError(ValueError):
    '''Unsupported Color Filter Array type'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s



# ----------------
# Auxiliar classes
# ----------------

class ExifImageLoader(AbstractImageLoader):

    BAYER_LETTER = ['B','G','R','G']
    BAYER_PTN_LIST = ('RGGB', 'BGGR', 'GRBG', 'GBRG')
    CFA_OFFSETS = {
        # Esto era segun mi entendimiento
        'RGGB' : {'R':{'x': 0,'y': 0}, 'Gr':{'x': 1,'y': 0}, 'Gb':{'x': 0,'y': 1}, 'B':{'x': 1,'y': 1}}, 
        'BGGR' : {'R':{'x': 1,'y': 1}, 'Gr':{'x': 1,'y': 0}, 'Gb':{'x': 0,'y': 1}, 'B':{'x': 0,'y': 0}},
        'GRBG' : {'R':{'x': 1,'y': 0}, 'Gr':{'x': 0,'y': 0}, 'Gb':{'x': 1,'y': 1}, 'B':{'x': 0,'y': 1}},
        'GBRG' : {'R':{'x': 0,'y': 1}, 'Gr':{'x': 0,'y': 0}, 'Gb':{'x': 1,'y': 1}, 'B':{'x': 1,'y': 0}},
    }

    def __init__(self, path, n_roi=None, channels=None):
        super().__init__(path, n_roi, channels)
        self._color_desc = None
        self._cfa = None
        self._biases = None
        self._white_levels = None
        self._exif()

    def _img(self):
        '''Gather as much rawpy image access as possible for efficiency'''
        with rawpy.imread(self._path) as img:
            self._read_img_metadata(img)

    def _read_img_metadata(self, img_desc):
        '''To be used in teh context of a image m¡context manager'''
        self._color_desc = img_desc.color_desc.decode('utf-8')
        self._cfa = ''.join([ self.BAYER_LETTER[img_desc.raw_pattern[row,column]] for row in (1,0) for column in (1,0)])
        self._biases = img_desc.black_level_per_channel
        self._white_levels = img_desc.camera_white_level_per_channel

    def _exif(self):
        with open(self._path, 'rb') as f:
            exif = exifread.process_file(f, details=True)
        if not exif:
            raise ValueError('Could not open EXIF metadata')
        width  = int(str(exif.get('EXIF ExifImageWidth')))
        height = int(str(exif.get('EXIF ExifImageLength')))
        # General purpose metadata
        self._shape = (height, width)
        self._roi =  Rect.from_normalized(self._shape[1], self._shape[0], self._n_roi, already_debayered=False)
        self._metadata['name'] = os.path.basename(self._path)
        self._metadata['roi'] = str(self._roi)
        self._metadata['channels'] = ' '.join(self._channels)
        # Metadata coming from EXIF
        self._metadata['exposure'] = fractions.Fraction(str(exif.get('EXIF ExposureTime', 0)))
        self._metadata['width'] = width
        self._metadata['height'] = height
        self._metadata['iso'] = str(exif.get('EXIF ISOSpeedRatings', None))
        self._metadata['camera'] = str(exif.get('Image Model', None)).strip()
        self._metadata['focal_length'] = fractions.Fraction(str(exif.get('EXIF FocalLength', 0)))
        self._metadata['f_number'] = fractions.Fraction(str(exif.get('EXIF FNumber', 0)))
        self._metadata['datetime'] = str(exif.get('Image DateTime', None))
        self._metadata['maker'] = str(exif.get('Image Make', None))
        self._metadata['note'] = str(exif.get('EXIF MakerNote', None)) # Useless fo far ...
        
    # ----------
    # Public API 
    # ----------

    def cfa_pattern(self):
        '''Returns the Bayer pattern as RGGB, BGGR, GRBG, GBRG strings'''
        if self._color_desc is None:
            self._img()
        if self._color_desc != 'RGBG':
            raise UnsupporteCFAError(self._color_desc)
        return self._cfa

    def saturation_levels(self):
        self._check_channels(err_msg="saturation_levels on G=(Gr+Gb)/2 channel not available")
        if self._white_levels is None:
            self._img()
        if self._white_levels is None:
            raise NotImplementedError("saturation_levels for this image not available using LibRaw")
        return [self._white_levels[CHANNELS.index(ch)] for ch in self._channels]

    def black_levels(self):
        self._check_channels(err_msg="black_levels on G=(Gr+Gb)/2 channel not available")
        if self._biases is None:
            self._img()
        return [self._biases[CHANNELS.index(ch)] for ch in self._channels]

    def load(self):
        '''Load a stack of Bayer colour planes selected by the channels sequence'''
        with rawpy.imread(self._path) as img:
            self._read_img_metadata(img)
            cfa_pattern = self._cfa
            raw_pixels_list = list()
            for channel in CHANNELS:
                x = self.CFA_OFFSETS[cfa_pattern][channel]['x']
                y = self.CFA_OFFSETS[cfa_pattern][channel]['y']
                raw_pixels = img.raw_image[y::2, x::2].copy() # This is the real debayering thing
                raw_pixels = self._trim(raw_pixels)
                raw_pixels_list.append(raw_pixels)
        return self._select_by_channels(raw_pixels_list) # Select the desired channels
        

    def statistics(self):
        '''In-place statistics calculation for RPi Zero'''
        self._check_channels(err_msg="In-place statistics on G=(Gr+Gb)/2 channel not available")
        with rawpy.imread(self._path) as img:
            # very imporatnt to be under the image context manager
            # when doing manipulations on img.raw_image
            self._read_img_metadata(img)
            cfa_pattern = self._cfa
            stats_list = list()
            for channel in CHANNELS:
                x = self.CFA_OFFSETS[cfa_pattern][channel]['x']
                y = self.CFA_OFFSETS[cfa_pattern][channel]['y']
                raw_pixels = img.raw_image[y::2, x::2]  # This is the real debayering thing
                raw_pixels = self._trim(raw_pixels)
                average, stddev = raw_pixels.mean(), raw_pixels.std()
                stats_list.append([average, stddev])
        return self._select_by_channels(stats_list)


