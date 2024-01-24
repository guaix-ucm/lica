# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# -------------------
# System wide imports
# -------------------

import os
import glob

# ---------
# Constants
# ---------

# ------------------
# Auxiliar functions
# ------------------

def file_paths(input_dir, files_filter):
    '''Given a directory and a file filter, returns full path list'''
    file_list =  [os.path.join(input_dir, fname) for fname in glob.iglob(files_filter, root_dir=input_dir)]
    if not file_list:
        raise OSError("File list is empty, review the directory path or filter")
    return file_list