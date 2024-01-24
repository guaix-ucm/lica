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

import logging

# ---------
# Constants
# ---------

log = logging.getLogger(__name__)

# ------------------
# Auxiliar functions
# ------------------

def write_csv(path, header, sequence, delimiter=';'):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, delimiter=delimiter)
        writer.writeheader()
        for row in sequence:
            writer.writerow(row)
    log.info("generated CSV file: %s", path)

