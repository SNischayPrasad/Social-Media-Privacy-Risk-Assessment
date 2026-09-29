"""
Shared pytest fixtures.

Every test gets a fresh Flask app backed by a temporary SQLite file, so tests
never touch the real database and never depend on each other.
"""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app  # noqa: E402
from backend.config import TestConfig  # noqa: E402
from backend.services.demo_profiles import (  # noqa: E402
    DEMO_PROFILE,
    fully_private_profile,
    fully_public_profile,
)
from backend.utils.security import rate_limiter  # noqa: E402


@pytest.fixture
def app(tmp_path):
    rate_limiter.reset()
    application = create_app(TestConfig, overrides={"DATABASE_PATH": str(tmp_path / "test.db")})
    yield application
    rate_limiter.reset()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def private_answers():
    return fully_private_profile()


@pytest.fixture
def public_answers():
    return fully_public_profile()


@pytest.fixture
def demo_answers():
    return dict(DEMO_PROFILE)


def profile_with(**overrides):
    """A fully private profile with a few answers changed - isolates one risk at a time."""
    answers = fully_private_profile()
    answers.update(overrides)
    return answers
