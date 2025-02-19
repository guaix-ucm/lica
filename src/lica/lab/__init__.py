from enum import IntEnum
from . import photodiode as photodiode
from . import ndfilters as ndfilters

class COL(StrEnum):
    """Calibration Table Columns"""

    WAVE = "Wavelength"
    RESP = "Responsivity"
    QE = "QE"
    TRANS = "Transmission"

# Unfortunately, the 1050 nm data point is not reached by the
# Scan.exe program, so we set wave end limit to 1049
class BENCH(IntEnum):
    """LICA Optical bench Wavelength range"""

    WAVE_START = 350
    WAVE_END = 1049

