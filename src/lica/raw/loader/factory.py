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

# ----------------
# Module Constants
# ----------------

FITS_EXTENSIONS = ('.fts', '.fit', '.fits')
EXIF_EXTENSIONS = ('.jpg','.jpeg', '.dng')

# ---------------------
# Thrid-party libraries
# ---------------------

# -----------
# Own package
# ----------

from .fits import FitsImageLoader
from .exif import ExifImageLoader
from .dng import DngImageLoader
from .simulation import SimulatedDarkImage
from .constants import FITS_EXTENSIONS, DNG_EXTENSIONS, JPG_EXTENSIONS


class ImageLoaderFactory:

	def image_from(self, path, n_roi=None, channels=None, simulated=False, **kwargs):
		extension = os.path.splitext(path)[1].lower()
		if simulated:
			image = SimulatedDarkImage(path, n_roi, channels, **kwargs)
		elif extension in FITS_EXTENSIONS:
			image = FitsImageLoader(path, n_roi, channels)
		elif extension in EXIF_EXTENSIONS:
			image = ExifImageLoader(path, n_roi, channels)
		else:
			raise IOError(f'Extension {extension} not handled by ImageLoaderFactory')
		return image


