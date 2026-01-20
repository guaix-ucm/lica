# ----------------------------------------------------------------------
# Copyright (c) 2025 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import re
import json
from datetime import datetime
from typing import Any, Union
from abc import ABC, abstractmethod
from logging import Logger
from collections import deque

# -------------------
# Third party imports
# -------------------

# --------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------


# -----------------------
# Module global variables
# -----------------------

# ----------------
# Module functions
# ----------------


# ----------
# Exceptions
# ----------


# -------
# Classes
# -------


class Payload(ABC):
    def __init__(self, logger: Logger, strict: bool):
        self.log = logger
        self.qprev = deque(maxlen=1)  # ring buffer 1 slot long
        self._rej_seq = 0
        self._rej_read = 0
        self._ok_payload = 0
        self._nok_payload = 0
        self._strict = strict  # Strict rejection by read period shorter than square wave period

    def is_rejected(self, message) -> bool:
        prev_msg = self.qprev[0]
        # This takes into account repeated sequence numbers
        if prev_msg["seq"] == message["seq"]:
            self._rej_seq += 1
            self.log.debug("Duplicate payload by identical #seq values: %s", message)
            return True
        if not self._strict:
            return False
        # This takes into account that the read period should be longer than the sqaure wave period
        aver_period = 2 / (prev_msg["freq"] + message["freq"])
        read_duration = (message["tstamp"] - prev_msg["tstamp"]).total_seconds()
        rejected = read_duration <= aver_period
        if rejected:
            self._rej_read += 1
            self.log.debug("Duplicate payload by short read times: %s ,prev=%s", message, prev_msg)
        return rejected

    @abstractmethod
    def decode(self, data: str) -> dict | None:
        """To be implemented in subclasses"""
        pass

    def report(self) -> None:
        self.log.info("Payload   [OK / NOK] = [%d / %d]", self._ok_payload, self._nok_payload)
        self.log.info(
            "Payload   rejections by [Dup #Seq / Tread] = [%d / %d]",
            self._rej_seq,
            self._rej_read,
        )


class OldPayload(Payload):
    """
    Decodes Old Style TESS payload:
    <fH 04606><tA +2987><tO +2481><mZ -0000>
    <fm 00080><tA +2987><tO +2481><mZ -0000>
    <fm-00000><tA +2987><tO +2481><mZ -0000>
    """

    UNSOLICITED_RESPONSES = (
        {
            "name": "Hz message",
            "pattern": r"^<fH([ +]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>",
        },
        {
            "name": "mHz message",
            "pattern": r"^<fm([ +-]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>",
        },
    )
    UNSOLICITED_PATTERNS = [re.compile(ur["pattern"]) for ur in UNSOLICITED_RESPONSES]

    def __init__(self, logger: Logger, strict: bool):
        super().__init__(logger, strict)
        self._i = 1
        self._rej_values = 0
        self.log.info("Using %s decoder", self.__class__.__name__)

    # ----------
    # Public API
    # ----------

    def decode(self, data: str, tstamp: datetime) -> dict | None:
        data = data.strip()
        result = None  # Assume bad result by default
        if len(data):
            self.log.debug("<== [%02d] %s", len(data), data)
            message = self._handle_unsolicited_response(data, tstamp)
            if message is not None:
                self._ok_payload += 1
                if len(self.qprev) > 0:
                    rejected = self.is_rejected(message)
                    prev = self.qprev.popleft()
                    self.qprev.append(message)
                    result = None if rejected else prev
                else:
                    self.qprev.append(message)
            else:
                self._nok_payload += 1
        return result

    def report(self) -> None:
        self.log.info("Payload   [OK / NOK] = [%d / %d]", self._ok_payload, self._nok_payload)
        self.log.info(
            "Payload   rejections by [Dup #Seq / Tread / Dup Values] = [%d / %d / %d]",
            self._rej_seq,
            self._rej_read,
            self._rej_values,
        )

    # --------------
    # Helper methods
    # --------------

    def is_rejected(self, message) -> bool:
        rejected = super().is_rejected(message)
        if rejected:
            return True
        # As serial messages do not have a sequnce number we introduce the
        # heuristic that a sample is duplicated if all the (freq, tamb, tsky)
        # readings are equal
        prev_msg = self.qprev[0]
        rejected = (
            True
            if (
                message["tamb"] == prev_msg["tamb"]
                and message["tsky"] == prev_msg["tsky"]
                and message["freq"] == prev_msg["freq"]
            )
            else False
        )
        if rejected:
            self._rej_values += 1
            self.log.debug("Duplicate payload by identical (freq, tamb, tsky) values: %s", message)
        return rejected

    def _match_unsolicited(self, line: str) -> tuple[dict | None, Any | None]:
        """Returns matched command descriptor or None"""
        for i, regexp in enumerate(OldPayload.UNSOLICITED_PATTERNS, 0):
            matchobj = regexp.search(line)
            if matchobj:
                #self.log.debug("Matched %s", OldPayload.UNSOLICITED_RESPONSES[i]["name"])
                return OldPayload.UNSOLICITED_RESPONSES[i], matchobj
        return None, None

    def _handle_unsolicited_response(self, line: str, tstamp: datetime) -> dict | None:
        """
        Handle unsolicited responses from spectess.
        Returns True if handled, False otherwise
        """
        ur, matchobj = self._match_unsolicited(line)
        if not ur:
            return None
        message = dict()
        message["tamb"] = float(matchobj.group(2)) / 100.0
        message["tsky"] = float(matchobj.group(3)) / 100.0
        message["zp"] = float(matchobj.group(4)) / 100.0
        message["tstamp"] = tstamp
        message["seq"] = self._i
        self._i += 1
        if ur["name"] == "Hz message":
            message["freq"] = float(matchobj.group(1)) / 1.0
        elif ur["name"] == "mHz message":
            message["freq"] = float(matchobj.group(1)) / 1000.0
        else:
            return None
        return message


class JsonPayload(Payload):
    """
    Decodes new JSON style TESS payload:
    """

    def __init__(self, logger: Logger, strict: bool):
        super().__init__(logger, strict)
        self.log.info("Using %s decoder", self.__class__.__name__)

    # --------------
    # Helper methods
    # --------------

    # ----------
    # Public API
    # ----------

    def decode(self, data: str, tstamp: datetime) -> dict | None:
        data = data.strip()
        self.log.debug("<== [%02d] %s", len(data), data)
        result = None  # assume bad result by default
        try:
            message = json.loads(data)
        except Exception as e:
            self._nok_payload += 1
            self.log.exception(e)
        else:
            if isinstance(message, dict):
                self._ok_payload += 1
                message["tstamp"] = tstamp
                message["seq"] = message["udp"]
                del message["udp"]
                if len(self.qprev) > 0:
                    rejected = self.is_rejected(message)
                    prev = self.qprev.popleft()
                    self.qprev.append(message)
                    result = None if rejected else prev
                else:
                    self.qprev.append(message)
        return result


# ---------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------

TessPayload = Union[JsonPayload, OldPayload]

__all__ = ["TessPayload", "JsonPayload", "OldPayload"]
