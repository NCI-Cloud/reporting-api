import time
import re
import ConfigParser
import MySQLdb
from MySQLdb import cursors
from webob import Response
import webob.exc
from apiversion import APIVersion

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbname = self.config.get('database', 'dbname')
		self.dbconn = MySQLdb.connect(
			host = self.config.get('database', 'hostname'),
			user = self.config.get('database', 'username'),
			passwd = self.config.get('database', 'password'),
			db = self.dbname
		)

	@classmethod
	def _version_identifier(cls):
		return "v1"

	def _safe_table_name(self, table_name):
		"""
		FIXME: How to defend against SQL injection?
		The test below is primitive but effective.
		PyMySQLdb has no placeholders for table names :-(
		"""
		if re.compile('^[a-zA-Z0-9_]+$').match(table_name):
			return True
		return False

	def _get_tables_comments(self, table_names):
		cursor = self.dbconn.cursor(cursors.Cursor)
		for table_name in table_names:
			if not self._safe_table_name(table_name):
				return webob.exc.HTTPForbidden()
		cursor.execute("SELECT table_comment FROM INFORMATION_SCHEMA.TABLES WHERE table_schema='" + self.dbname + "' AND table_name IN ('" + "','".join(table_names) + "');")
		rows = cursor.fetchall()
		return [ row[0] for row in rows]

	def _get_table_comment(self, table_name):
		return self._get_tables_comments([ table_name ])[0]

	def ReportsList(self, args):
		cursor = self.dbconn.cursor(cursors.Cursor)
		cursor.execute('SHOW TABLES;')
		rows = cursor.fetchall()
		return Response(content_type = 'application/json', body = self._resultset_to_json([
			{
				'name': row[0],
				'description': self._get_table_comment(row[0]),
				'lastUpdated': time.asctime() # TODO
			} for row in rows
		]))

	def ReportDetail(self, args):
		table_name = args['report']
		return Response(content_type = 'application/json', body = self._resultset_to_json({
			'name': table_name,
			'description': self._get_table_comment(table_name),
				'lastUpdated': time.asctime() # TODO
		}))

	def ReportResultSet(self, args):
		table_name = args['report']
		if self._safe_table_name(table_name):
			try:
				cursor = self.dbconn.cursor(cursors.DictCursor)
				cursor.execute('SELECT * FROM ' + table_name + ';')
			except:
				# Don't leak information about the database
				return webob.exc.HTTPNotFound()
			return Response(content_type = 'application/json', body = self._resultset_to_json(cursor.fetchall()))
		return webob.exc.HTTPForbidden()

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
