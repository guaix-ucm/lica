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
from .roi import Roi, NormRoi
from .abstract import AbstractImageLoader

# ---------
# Constants
# ---------

log = logging.getLogger(__name__)

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
        self._shape = None
        self._color_desc = None
        self._cfa = None
        self._biases = None
        self._white_levels = None
        #self._exif() # read exif metadata
        #self._raw() # read raw metadata


    def _raw_metadata(self, img):
        '''To be used in teh context of an image context manager'''
        self._color_desc = img.color_desc.decode('utf-8')
        self._cfa = ''.join([ self.BAYER_LETTER[img.raw_pattern[row,column]] for row in (1,0) for column in (1,0)])
        self._biases = img.black_level_per_channel
        self._white_levels = img.camera_white_level_per_channel
        self._metadata['pedestal'] = self.black_levels()
        self._metadata['bayerpat'] = self._cfa
        self._metadata['colordesc'] = self._color_desc

    def _raw(self):
        with rawpy.imread(self._path) as img:
            log.debug(" -----> LibRaw I/O for %s", os.path.basename(self._path))
            self._raw_metadata(img)


    def _exif(self):
        with open(self._path, 'rb') as f:
            log.debug(" -----> EXIF I/O for %s", os.path.basename(self._path))
            exif = exifread.process_file(f, details=True)
        if not exif:
            raise ValueError('Could not open EXIF metadata')
        width  = int(str(exif.get('EXIF ExifImageWidth')))
        height = int(str(exif.get('EXIF ExifImageLength')))
        self._name = os.path.basename(self._path)
        self._shape = (height//2, width//2)
        self._roi =  Roi.from_normalized_roi(width, height, self._n_roi, already_debayered=False)
        # General purpose metadata
        self._metadata['name'] = self._name
        self._metadata['roi'] = str(self._roi)
        self._metadata['channels'] = ' '.join(self._channels)
        # Metadata coming from EXIF
        self._metadata['exposure'] = fractions.Fraction(str(exif.get('EXIF ExposureTime', 0)))
        self._metadata['width'] = width // 2
        self._metadata['height'] = height //2
        self._metadata['iso'] = str(exif.get('EXIF ISOSpeedRatings', None))
        self._metadata['camera'] = str(exif.get('Image Model', None)).strip()
        self._metadata['focal_length'] = fractions.Fraction(str(exif.get('EXIF FocalLength', 0)))
        self._metadata['f_number'] = fractions.Fraction(str(exif.get('EXIF FNumber', 0)))
        self._metadata['datetime'] = str(exif.get('Image DateTime', None))
        self._metadata['maker'] = str(exif.get('Image Make', None))
        self._metadata['note'] = str(exif.get('EXIF MakerNote', None)) # Useless fo far ...
        self._metadata['log-gain'] = None  # Not known until load time
        self._metadata['xpixsize'] = None  # Not usually available in EXIF headers
        self._metadata['ypixsize'] = None  # Not usually available in EXIF headers
        self._metadata['imagetyp'] = None  # using an heuristic based on file names
 
    # ----------
    # Public API 
    # ----------

    def metadata(self):
        if self._name is None:
            self._exif()
        if self._cfa is None:
            self._raw()
        return self._metadata

    def cfa_pattern(self):
        '''Returns the Bayer pattern as RGGB, BGGR, GRBG, GBRG strings'''
        if self._color_desc is None:
            self._raw()
        if self._color_desc != 'RGBG':
            raise UnsupporteCFAError(self._color_desc)
        return self._cfa

    def saturation_levels(self):
        self._check_channels(err_msg="saturation_levels on G=(Gr+Gb)/2 channel not available")
        if self._white_levels is None:
            self._raw()
        if self._white_levels is None:
            raise NotImplementedError("saturation_levels for this image not available using LibRaw")
        return tuple(self._white_levels[CHANNELS.index(ch)] for ch in self._channels)

    def black_levels(self):
        self._check_channels(err_msg="black_levels on G=(Gr+Gb)/2 channel not available")
        if self._biases is None:
            self._raw()
        return tuple(self._biases[CHANNELS.index(ch)] for ch in self._channels)

    def load(self):
        '''Load a stack of Bayer colour planes selected by the channels sequence'''
        if self._name is None:
            self._exif()
        with rawpy.imread(self._path) as img:
            self._raw_metadata(img)
            raw_pixels_list = list()
            for channel in CHANNELS:
                x = self.CFA_OFFSETS[self._cfa][channel]['x']
                y = self.CFA_OFFSETS[self._cfa][channel]['y']
                raw_pixels = img.raw_image[y::2, x::2].copy() # This is the real debayering thing
                raw_pixels = self._trim(raw_pixels)
                raw_pixels_list.append(raw_pixels)
        return self._select_by_channels(raw_pixels_list) # Select the desired channels

    def statistics(self):
        '''In-place statistics calculation for RPi Zero'''
        self._check_channels(err_msg="In-place statistics on G=(Gr+Gb)/2 channel not available")
        if self._name is None:
            self._exif()
        with rawpy.imread(self._path) as img:
            # very imporatnt to be under the image context manager
            # when doing manipulations on img.raw_image
            self._raw_metadata(img)
            stats_list = list()
            for channel in CHANNELS:
                x = self.CFA_OFFSETS[self._cfa][channel]['x']
                y = self.CFA_OFFSETS[self._cfa][channel]['y']
                raw_pixels = img.raw_image[y::2, x::2]  # This is the real debayering thing
                raw_pixels = self._trim(raw_pixels)
                average, stddev = raw_pixels.mean(), raw_pixels.std()
                stats_list.append([average, stddev])
        return self._select_by_channels(stats_list)
