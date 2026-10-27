"""
The application code must not use deprecated Qt or library functions
(they produced hundreds of warnings in the test runs and will break with
a future PySide6). The scenario runs in a separate process (fresh imports,
so that warnings issued only when a module is imported are found too) and
reports every DeprecationWarning that comes from the application's files.
"""
import os
import subprocess
import sys
from unittest import TestCase

import signalflowgrapher


class TestNoDeprecatedApi(TestCase):
    def test_gui_scenario_raises_no_deprecation_warning(self):
        src_dir = os.path.dirname(os.path.dirname(signalflowgrapher.__file__))
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen",
                   PYTHONPATH=src_dir)
        result = subprocess.run(
            [sys.executable, "-m",
             "signalflowgrapher.tests.gui.deprecation_scenario"],
            env=env, capture_output=True, text=True, timeout=300)
        self.assertEqual(0, result.returncode,
                         "deprecated API used by the application:\n"
                         + result.stdout[-2500:] + result.stderr[-1500:])
        self.assertIn("scenario finished", result.stdout)
        self.assertIn("0 deprecation warning(s)", result.stdout)
