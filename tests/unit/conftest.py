import logging

import pytest


@pytest.fixture(autouse=True)
def reset_app_logger():
    app_logger = logging.getLogger("app")
    original_level = app_logger.level
    original_propagate = app_logger.propagate
    original_handlers = app_logger.handlers[:]
    yield
    app_logger.setLevel(original_level)
    app_logger.propagate = original_propagate
    app_logger.handlers = original_handlers
