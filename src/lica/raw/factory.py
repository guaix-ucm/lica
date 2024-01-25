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



class ImageFactory:

	def image_from(self, path):
		extension = os.path.splitext(path)[1]
		if extension in FITS_EXTENSIONS:
			image = FitImage(path)
		else
			image = ExifImage(path)
		return image
