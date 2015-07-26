import time
import re
import json
import ConfigParser
import MySQLdb
from MySQLdb import cursors
from webob import Response
import webob.exc
from apiversion import APIVersion

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbconn = MySQLdb.connect(
			host = self.config.get('database', 'hostname'),
			user = self.config.get('database', 'username'),
			passwd = self.config.get('database', 'password'),
			db = self.config.get('database', 'dbname')
		)

	@classmethod
	def _version_identifier(cls):
		return "v1";

	def ReportsList(self, args):
		cursor = self.dbconn.cursor(cursors.Cursor);
		cursor.execute('SHOW TABLES;')
		tables = cursor.fetchall()
		return Response(content_type = 'application/json', body = json.dumps([
			{
				'name': row[0],
				'description': 'TODO',
				'lastUpdated': time.asctime() # TODO
			} for row in tables
		]))

	def ReportDetail(self, args):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "Report detail" }))

	def ReportResultSet(self, args):
		table_name = args['report']
		# FIXME: How to defend against SQL injection?
		# The test below is primitive but effective.
		# PyMySQLdb has no placeholders for table names :-(
		if re.compile('^[a-zA-Z0-9_]+$').match(table_name):
			try:
				cursor = self.dbconn.cursor(cursors.DictCursor)
				cursor.execute('SELECT * FROM ' + table_name + ';')
			except:
				# Don't leak information about the database
				return webob.exc.HTTPNotFound()
			return Response(content_type = 'application/json', body = json.dumps(cursor.fetchall()))
		return webob.exc.HTTPForbidden();

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
