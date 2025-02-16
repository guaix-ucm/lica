# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import datetime
import asyncio

# -----------------
# Third Party imports
# -------------------

import serial_asyncio

# --------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# -------------------
# Auxiliary functions
# -------------------


class UDPTransport(asyncio.DatagramProtocol):
    def __init__(self, parent, port=2255):
        self.parent = parent
        self.log = parent.log
        self.local_host = "0.0.0.0"
        self.local_port = port
        self.log.info("Using %s Transport", self.__class__.__name__)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, payload, addr):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.parent.handle_readings(payload.rstrip(), now)

    def connection_lost(self, exc):
        if not self.on_conn_lost.cancelled():
            self.on_conn_lost.set_result(True)

    async def readings(self):
        loop = asyncio.get_running_loop()
        self.on_conn_lost = loop.create_future()
        transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: self, local_addr=(self.local_host, self.local_port)
        )
        try:
            await self.on_conn_lost
        finally:
            self.transport.close()


class TCPTransport(asyncio.Protocol):
    def __init__(self, parent, host="192.168.4.1", port=23):
        self.parent = parent
        self.log = parent.log
        self.host = host
        self.port = port
        self.log.info("Using %s Transport", self.__class__.__name__)

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.parent.handle_readings(data, now)

    def connection_lost(self, exc):
        if not self.on_conn_lost.cancelled():
            self.on_conn_lost.set_result(True)

    async def readings(self):
        loop = asyncio.get_running_loop()
        self.on_conn_lost = loop.create_future()
        transport, self.protocol = await loop.create_connection(lambda: self, self.host, self.port)
        try:
            await self.on_conn_lost
        finally:
            self.transport.close()


import logging

log = logging.getLogger(__name__.split(".")[-1])


class SerialTransport(asyncio.Protocol):
    def __init__(self, parent, port="/dev/ttyUSB0", baudrate=9600):
        self.parent = parent
        self.log = parent.log
        self.port = port
        self.baudrate = baudrate
        self.on_conn_lost = None
        self.transport = None
        self.log.info("Using %s Transport", self.__class__.__name__)

    def connection_made(self, transport):
        log.info("Connection made!")
        self.transport = transport
        # You can manipulate Serial object via transport
        # transport.serial.rts = False  # You can manipulate Serial object via transport

    def data_received(self, data: bytes):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.parent.handle_readings(data, now)

    def connection_lost(self, exc):
        log.info("Connection lost!")
        if not self.on_conn_lost.cancelled():
            self.on_conn_lost.set_result(True)

    def write(self, data: bytes):
        self.transport.write(data)

    async def readings(self):
        """This is meant to be a task"""
        loop = asyncio.get_running_loop()
        self.on_conn_lost = loop.create_future()
        transport, self.protocol = await serial_asyncio.create_serial_connection(
            lambda: self, self.port, self.baudrate
        )
        try:
            await self.on_conn_lost
        finally:
            self.transport.close()
