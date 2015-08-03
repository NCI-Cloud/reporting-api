#!/usr/bin/python

import sys, os
from paste.deploy import loadapp, loadserver
from paste import httpserver

if __name__ == '__main__':
	paste_config = 'paste.config'
	reporting_app = loadapp('config:' + paste_config, relative_to=os.path.dirname(os.path.realpath(__file__)))
	server = loadserver('config:' + paste_config, relative_to=os.path.dirname(os.path.realpath(__file__)))
	server(reporting_app)
