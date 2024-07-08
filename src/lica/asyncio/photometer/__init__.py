# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ---------------------
# Third party libraries
# ---------------------

import enum
import decouple

# ---------
# Constants
# ---------

class Role(enum.IntEnum):
    REF = 1
    TEST = 0

    def tag(self):
        return f"{self.name:.<4s}"

    def __str__(self):
        return f"{self.name.lower()}"

    def __iter__(self):
            return self

    def __next__(self):
            return Role.TEST if self is Role.REF else Role.REF

class Model(enum.Enum):
    # Photometer models
    TESSW  = "TESS-W"
    TESSP  = "TESS-P"
    TAS    = "TAS"
    TESS4C = "TESS4C"


def other(role: Role) -> Role:
    return next(role)

def endpoint(role: Role) -> str:
    env_var = 'REF_ENDPOINT' if role is Role.REF else 'TEST_ENDPOINT'
    return decouple.config(env_var)

