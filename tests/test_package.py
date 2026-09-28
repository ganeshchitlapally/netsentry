import importlib

import pytest

import netsentry

SUBPACKAGES = ["data", "features", "models", "serving", "agent", "eval"]


def test_version_is_set():
    assert netsentry.__version__


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_import(name: str):
    importlib.import_module(f"netsentry.{name}")
