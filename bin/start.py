#!/usr/bin/python

import sys, os
from paste.deploy import loadapp, loadserver
from paste import httpserver

if __name__ == '__main__':
	realfile = os.path.realpath(__file__)
	realdir = os.path.dirname(realfile)
	pardir = os.path.realpath(os.path.join(realdir, os.pardir))
	paste_config = os.path.join(pardir, 'paste.config')
	sys.path.append(pardir)
	reporting_app = loadapp('config:' + paste_config)
	server = loadserver('config:' + paste_config)
	server(reporting_app)
