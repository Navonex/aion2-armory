"""Logging: einheitliches Format."""
from __future__ import annotations

import logging


def setup() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # httpx meldet jede Anfrage an die AION-2-Website; Warnungen reichen
    logging.getLogger("httpx").setLevel(logging.WARNING)
