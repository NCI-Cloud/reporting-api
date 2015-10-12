#!/usr/bin/python

import sys, os
from paste.deploy import loadapp, loadserver
import logging

if __name__ == '__main__':
	logging.basicConfig(filename = '/var/log/reporting-api.log', level = logging.INFO)
	realfile = os.path.realpath(__file__)
	realdir = os.path.dirname(realfile)
	pardir = os.path.realpath(os.path.join(realdir, os.pardir))
	confdir = os.path.join(pardir, 'conf')
	paste_config = os.path.join(confdir, 'paste.config')
	sys.path.append(pardir)
	reporting_app = loadapp('config:' + paste_config)
	server = loadserver('config:' + paste_config)
	server(reporting_app)
