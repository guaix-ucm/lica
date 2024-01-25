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

from .fits import FitsImageLoader
from .exif import ExifImageLoader
from .constants import FITS_EXTENSIONS


class ImageLoaderFactory:

	def image_from(self, path):
		extension = os.path.splitext(path)[1]
		if extension in FITS_EXTENSIONS:
			image = FitImage(path)
		else:
			image = ExifImageLoader(path)
		return image


