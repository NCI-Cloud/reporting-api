#!/usr/bin/python

from paste.translogger import TransLogger

def factory(config, **settings):
	def filter(app):
		config.update(settings);
		return TransLogger(app, setup_console_handler = True)
	return filter
