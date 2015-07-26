import json
import ConfigParser
import MySQLdb
from MySQLdb import cursors
from webob import Response
from apiversion import APIVersion

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbconn = MySQLdb.connect(
			host = self.config.get('database', 'hostname'),
			user = self.config.get('database', 'username'),
			passwd = self.config.get('database', 'password'),
			db = self.config.get('database', 'dbname'),
			cursorclass = MySQLdb.cursors.DictCursor
		)
		self.cursor = self.dbconn.cursor()

	@classmethod
	def _version_identifier(cls):
		return "v1";

	def ReportsList(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "List of reports" }))

	def ReportDetail(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "Report detail" }))

	def ReportResultSet(self):
		self.cursor.execute("""SELECT * FROM project_resource_use;""")
		return Response(content_type = 'application/json', body = json.dumps(self.cursor.fetchall()))

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
