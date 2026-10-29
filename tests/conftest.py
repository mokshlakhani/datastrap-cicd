"""Shared test setup: lets tests import the app's modules from the repo root."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def demo():
    """The fictional demo dataset shipped with the app (no personal data, no network)."""
    with open(os.path.join(ROOT, "demo_data.json")) as fh:
        return json.load(fh)
