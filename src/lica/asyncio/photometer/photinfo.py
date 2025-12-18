# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import re
import datetime
from logging import Logger
from typing import Union

# -----------------
# Third Party imports
# -------------------

import aiohttp
from sqlalchemy import text


from . import Role

# ------------------
# Auxiliar functions
# ------------------


def formatted_mac(mac):
    """'Corrects TESS-W MAC strings to be properly formatted"""
    return ":".join(f"{int(x, 16):02X}" for x in mac.split(":"))


# -------
# Classes
# -------


class HTMLInfo:
    """
    Get the photometer by parsing the HTML photometer home page.
    Set the new ZP by using the same URL as the HTML form displayed for humans
    """

    CONFLICTIVE_FIRMWARE = ("Nov 25 2021 v 3.2",)

    GET_INFO = {
        # These apply to the /config page
        "model": re.compile(r"([-0-9A-Z]+)\s+Settings\."),
        "name": re.compile(r"(stars\d+)"),
        "mac": re.compile(
            r"MAC: ([0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2})"
        ),
        "zp": re.compile(r"(ZP|CI|CI 1): (\d{1,2}\.\d{1,2})"),
        # 'zp'    : re.compile(r"Const\.: (\d{1,2}\.\d{1,2})"),
        "freq_offset": re.compile(r"Offset mHz: (\d{1,2}\.\d{1,2})"),
        # Non-greedy matching until <br>
        "firmware": re.compile(r"Compiled: (.+?)<br>"),
        "firmware_ext": re.compile(r"Firmware v: (\d+\.\d+)<br>"),
        # This applies to the /setconst?cons=nn.nn or /SetZP?nZP1=nn.nn pages
        "flash": re.compile(r"New Zero Point (\d{1,2}\.\d{1,2})|CI 4 chanels:"),
    }

    def __init__(self, logger: Logger, addr: str, role: Role = Role.TEST):
        self.log = logger
        self.addr = addr
        self.role = role
        self.log.info("Using %s", self.__class__.__name__)

    # ----------------------------
    # Photometer Control interface
    # ----------------------------

    async def get_info(self, timeout: int = 4):
        """
        Get photometer information.
        """
        result = {}
        url = self._make_state_url()
        self.log.info("[HTTP GET] info from %s", url)
        timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                text = await response.text()
        matchobj = self.GET_INFO["name"].search(text)
        if not matchobj:
            self.log.error("name not found!. Check unit's name")
            result["name"] = None
        else:
            result["name"] = matchobj.groups(1)[0]
        matchobj = self.GET_INFO["mac"].search(text)
        if not matchobj:
            self.log.error("MAC not found!")
            result["mac"] = None
        else:
            result["mac"] = formatted_mac(matchobj.groups(1)[0])
        matchobj = self.GET_INFO["zp"].search(text)
        if not matchobj:
            self.log.error("ZP not found!")
            result["zp"] = None
        else:
            # Beware the seq index, it is not 0 as usual. See the regexp!
            result["zp"] = float(matchobj.groups(1)[1])
        matchobj = self.GET_INFO["firmware"].search(text)
        if not matchobj:
            self.log.error("Firmware not found!")
            result["firmware"] = None
        else:
            result["firmware"] = matchobj.groups(1)[0]
        matchobj = self.GET_INFO["firmware_ext"].search(text)
        if matchobj:
            result["firmware"] = result["firmware"] + " v" + matchobj.groups(1)[0]
        if result["firmware"] in self.CONFLICTIVE_FIRMWARE:
            self.log.error("Conflictive firmware: %s", result["firmware"])
        matchobj = self.GET_INFO["freq_offset"].search(text)
        if not matchobj:
            self.log.warn("Frequency offset not found, defaults to None")
            result["freq_offset"] = None
        else:
            result["freq_offset"] = float(matchobj.groups(1)[0]) / 1000.0
        matchobj = self.GET_INFO["model"].search(text)
        if not matchobj:
            self.log.warn("Model not found, defaults to None")
            result["model"] = None
        else:
            result["model"] = matchobj.groups(1)[0]
        # Up to now, we don't know what the sensor model is.
        result["sensor"] = None
        self.log.warn("Sensor model set to %s by default", result["sensor"])
        return result

    async def save_zero_point(self, zero_point, timeout=4):
        """
        Writes Zero Point to the device.
        """
        label = str(self.role)
        result = {}
        result["tstamp"] = datetime.datetime.now(datetime.timezone.utc)
        url = self._make_save_url()
        # params = [('cons', '{0:0.2f}'.format(zero_point))]
        # Paradoxically, the photometer uses an HTTP GET method to write a ZP ....
        params = ({"cons": "%0.2f" % (zero_point)}, {"nZP1": "%0.2f" % (zero_point)})
        urls = (self._make_save_url(), self._make_save_url2())
        written_zp = False
        timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i, (url, param) in enumerate(zip(urls, params), start=1):
                async with session.get(url, params=param) as response:
                    text = await response.text()
                matchobj = self.GET_INFO["flash"].search(text)
                if matchobj:
                    self.log.info("[HTTP GET] %s %s", url, param)
                    result["zp"] = float(matchobj.groups(1)[0]) if i == 1 else zero_point
                    written_zp = True
                    break
        if not written_zp:
            raise IOError("{:6s} ZP not written. Check save URL and query params".format(label))
        result["zp"] = float(matchobj.groups(1)[0])
        return result

    # --------------
    # Helper methods
    # --------------

    def _make_state_url(self):
        return f"http://{self.addr}/config"

    def _make_save_url(self):
        return f"http://{self.addr}/setconst"

    def _make_save_url2(self):
        """New Write ZP URL from firmware version starting on 16 June 2023"""
        return f"http://{self.addr}/SetZP"


class DBaseInfo:
    def __init__(self, logger: Logger, engine, role: Role = Role.REF):
        self.log = logger
        self.log.info("Using %s", self.__class__.__name__)
        self.engine = engine
        self.role = role

    # ----------------------------
    # Photometer Control interface
    # ----------------------------

    async def save_zero_point(self, zero_point: float, timeout=4):
        """
        Writes Zero Point to the REF device.
        """
        zero_point = str(zero_point)
        async with self.engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        "UPDATE config_t SET value = :value WHERE section = :section AND property = :property"
                    ),
                    {"section": "ref-device", "property": "zp", "value": zero_point},
                )
            except Exception:
                await conn.rollback()
            else:
                await conn.commit()

    async def get_info(self, timeout):
        """
        Get REF photometer information from the database.
        """
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT property, value FROM config_t WHERE section = :section"),
                {"section": "ref-device"},
            )
            result = {row[0]: row[1] for row in result}
        return result


TessInfo = Union[HTMLInfo, DBaseInfo]

__all__ = ["TessInfo", "HTMLInfo", "DBaseInfo"]
