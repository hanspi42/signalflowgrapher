# -*- coding: utf-8 -*-
"""
This skript can be usde instead of starting the tool with
python -m signalflowgrapher.

@author: hanspi42
"""

from signalflowgrapher import app
import sys

app.run(sys.argv[1:])