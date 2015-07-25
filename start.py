#!/usr/bin/python

import sys, os
from paste.deploy import loadapp

reporting_app = loadapp('config:paste.config', relative_to=os.path.dirname(os.path.realpath(__file__)))
