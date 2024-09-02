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

import csv

# ---------
# Constants
# ---------

# ------------------
# Auxiliar functions
# ------------------


def write_csv(path, header, sequence, delimiter=';'):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=header, delimiter=delimiter)
        writer.writeheader()
        for row in sequence:
            writer.writerow(row)


def read_csv(path, delimiter=';'):
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        sequence = [row for row in reader]
        return sequence
