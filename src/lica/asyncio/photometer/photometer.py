# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from datetime import datetime
from typing import Tuple, AsyncIterator, Any

# ---------------------
# Third party libraries
# ---------------------


# ------------
# Own packages
# ------------

from . import Role

from .protocol import TessProtocol
from .payload import TessPayload
from .photinfo import TessInfo


class Photometer:
    def __init__(self, role: Role):
        self.role = role
        self.log = logging.getLogger(role.tag())
        self.decoder = None
        self.transport = None
        self.info = None

    def attach(self, transport: TessProtocol, info: TessInfo, decoder: TessPayload):
        self.decoder = decoder
        self.transport = transport
        self.info = info

    # ----------
    # Public API
    # ----------

    def __aiter__(self) -> AsyncIterator[Tuple[datetime, str] | None]:
        """
        Método para inicializar el iterador asíncrono.
        Retorna un AsyncIterator
        """
        return aiter(self)

    async def __anext__(self) -> Tuple[datetime, str] | None:
        """
        Método para obtener el siguiente ítem asincrónico.
        Retorna una tupla de tstamp y el mensaje o bien None si el mensaje no es valido en la decodificación
        o lanza StopAsyncIteration para finalizar la iteración.
        """
        tstamp, message = await anext(self.transport)
        return self.decoder.decode(data=message, tstamp=tstamp)

    async def __aenter__(self) -> "Photometer":
        """
        Context manager that opens/closes the underlying communication interface.
        """
        await self.transport.open()
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: BaseException | None, exc_tb: Any | None
    ) -> bool | None:
        """
        Context manager that opens/closes the underlying communication interface.
        """
        self.decoder.report()
        self.transport.close()
        return False

    async def open(self) -> None:
        """Opens the underlyung protocol transport"""
        await self.transport.open()

    # to be used in 'async for phot.readings' or 'while/anext(phot.readings)' loops
    @property
    def readings(self):
        return self

    async def get_info(self, timeout=5):
        return await self.info.get_info(timeout)

    async def save_zero_point(self, zero_point):
        return await self.info.save_zero_point(zero_point)
