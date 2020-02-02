import os
import subprocess

import pytest

from hslog import LogParser


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DATA_DIR = os.path.join(BASE_DIR, "logdata")
LOG_DATA_GIT = "https://github.com/HearthSim/hsreplay-test-data"


def pytest_addoption(parser):
	parser.addoption(
		"--regression-suite", action="store_true", help="Run regression test suite"
	)


def pytest_configure(config):
	if not os.path.exists(LOG_DATA_DIR):
		proc = subprocess.Popen(["git", "clone", LOG_DATA_GIT, LOG_DATA_DIR])
		assert proc.wait() == 0
	config.addinivalue_line(
		"markers", "regression_suite: mark test to run only during regression suite"
	)


def pytest_runtest_setup(item):
	if "regression_suite" in item.keywords:
		if not item.config.getoption("regression_suite"):
			pytest.skip("need --regression-suite option to run")


def logfile(path):
	return os.path.join(LOG_DATA_DIR, "hslog-tests", path)


@pytest.fixture
def parser():
	return LogParser()
