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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

url = decouple.config("DATABASE_URL")

# 'check_same_thread' is only needed in SQLite ....
engine = create_engine(url, connect_args={"check_same_thread": False})


Session = sessionmaker(engine, expire_on_commit=True)

__all__ = ["url", "engine",  "Session"]
