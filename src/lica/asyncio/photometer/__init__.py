# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# -------------------
# System wide imports
# -------------------

from enum import IntEnum, StrEnum
from datetime import datetime
from typing import Dict, Union

# ---------------------
# Third party libraries
# ---------------------

import decouple

# Typing the message received by photometers
Message = Dict[str, Union[str, int, float, datetime]]

# ---------
# Constants
# ---------


class Role(IntEnum):
    REF = 1
    TEST = 0

    def tag(self):
        return f"{self.name:.<4s}"

    def __str__(self):
        return f"{self.name.lower()}"

    def __repr__(self):
        return f"{self.name.upper()}"

    def __iter__(self):
        return self

    def __next__(self):
        return Role.TEST if self is Role.REF else Role.REF

    def other(self) -> "Role":
        return next(self)

    def endpoint(self) -> str:
        env_var = "REF_ENDPOINT" if self is Role.REF else "TEST_ENDPOINT"
        return decouple.config(env_var)


class Model(StrEnum):
    # Photometer models
    TESSW = "TESS-W"
    TESSP = "TESS-P"
    TAS = "TAS"
    TESS4C = "TESS4C"
    TESSWDL = "TESS-WDL"


class Sensor(StrEnum):
    TSL237 = "TSL237"
    S970501DT = "S9705-01DT"
