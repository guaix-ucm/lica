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
# ----------

from .fits import FitsImage
from .exif import ExifImage

# ---------
# Constants
# ---------

LABELS = (('Red', 'R'), ('Green r','Gr'), ('Green b', 'Gb'), ('Blue', 'B'))
CHANNELS = ('R', 'Gr', 'Gb', 'B')

FITS_EXTENSIONS = ('.fts', '.fit', '.fits')

class ImageFactory:

	def imageFor(self, path):
		extension = os.path.splitext(path)[1]:
		if extension in FITS_EXTENSIONS:
			image = FitImage(path)
		else
			image = ExifImage(path)
		return image
