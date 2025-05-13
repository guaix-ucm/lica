# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

# ---------------------
# Third party libraries
# ---------------------

import decouple

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

url = decouple.config("DATABASE_URL")

# 'check_same_thread' is only needed in SQLite ....
engine = create_async_engine(url, connect_args={"check_same_thread": False})


AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

__all__ = ["url", "engine", "AsyncSession"]
