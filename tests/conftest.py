import os
import sys

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from handgame.gui.integration_controller import GUIIntegrationController


@pytest.fixture(scope="session")
def qapp():
    # A QApplication (not bare QCoreApplication) so widget tests can construct
    # QWidgets; "offscreen" keeps it headless on CI. Everything the non-GUI
    # tests need from QCoreApplication is a subset of QApplication.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def controller(qapp):
    ctrl = GUIIntegrationController()
    yield ctrl
    ctrl.shutdown()
