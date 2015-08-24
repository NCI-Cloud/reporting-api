from datetime import datetime
from common.sql import SQL
import ConfigParser
import MySQLdb
from MySQLdb import cursors
from _mysql_exceptions import OperationalError
import webob.exc
from common.apiversion import APIVersion

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbname = self.config.get('database', 'dbname')
		if not SQL._safe_identifier(self.dbname):
			raise ValueError("Unsafe DB name '%s'" % self.dbname)
		self.dbconn = MySQLdb.connect(
			host = self.config.get('database', 'hostname'),
			user = self.config.get('database', 'username'),
			passwd = self.config.get('database', 'password'),
			db = self.dbname
		)

	@classmethod
	def _version_identifier(cls):
		return "v1"

	@classmethod
	def _get_links(cls):
		return dict(
			reports = '/v1/reports'
		)

	@classmethod
	def _get_report_links(cls, report):
		return dict(
			self = '/v1/reports/' + report
		)

	def _before_db(self):
		"""
		MySQL-specific: attempt to reconnect if our connection has timed out
		"""
		try:
			self.dbconn.ping(True)
		except OperationalError:
			"""
			Probably just a stale connection.
			If something worse has gone wrong, we will see it soon anyway.
			"""
			pass

	def _get_tables_comments(self, table_names):
		self._before_db()
		cursor = self.dbconn.cursor(cursors.Cursor)
		for table_name in table_names:
			if not SQL._safe_identifier(table_name):
				return webob.exc.HTTPForbidden()
		cursor.execute("SELECT table_comment FROM INFORMATION_SCHEMA.TABLES WHERE table_schema='" + self.dbname + "' AND table_name IN ('" + "','".join(table_names) + "');")
		rows = cursor.fetchall()
		return [ row[0] for row in rows]

	def _get_table_comment(self, table_name):
		return self._get_tables_comments([ table_name ])[0]

	def _get_table_lastupdates(self, table_names):
		self._before_db()
		cursor = self.dbconn.cursor(cursors.Cursor)
		for table_name in table_names:
			if not SQL._safe_identifier(table_name):
				return webob.exc.HTTPForbidden()
		cursor.execute("SELECT ts FROM metadata WHERE table_name IN ('" + "','".join(table_names) + "');")
		return [ row[0] for row in cursor.fetchall() ]

	def _get_table_lastupdate(self, table_name):
		rows = self._get_table_lastupdates([ table_name ])
		if rows:
			return rows[0]
		return datetime.utcfromtimestamp(0).isoformat()

	def _get_report_details(self, report_name):
		return dict(
				name = report_name,
				description = self._get_table_comment(report_name),
				lastUpdated = self._get_table_lastupdate(report_name),
				links = self._get_report_links(report_name)
			)

	def ReportsList(self, req, args):
		self._before_db()
		cursor = self.dbconn.cursor(cursors.Cursor)
		cursor.execute('SHOW TABLES;')
		rows = cursor.fetchall()
		details = [ self._get_report_details(row[0]) for row in rows ]
		return ( details, None )

	def ReportResultSet(self, req, args):
		table_name = args['report']
		del args['report']
		if not SQL._safe_identifier(table_name):
			return webob.exc.HTTPForbidden()
		for (key, val) in args.items():
			if not SQL._safe_identifier(key):
				return webob.exc.HTTPForbidden()
			if len(val) != 1:
				return webob.exc.HTTPBadRequest("No or multiple values passed for parameter '%s'" % key)
			for ent in val:
				if not SQL._safe_identifier(ent):
					return webob.exc.HTTPForbidden()
		headers = None
		query = 'SELECT * FROM `' + table_name + '`'
		if args:
			query += ' WHERE '
			criteria = []
			for (key, val) in args.items():
				criteria.append("`" + key + "`='" + val[0] + "'")
			query += ' AND '.join(criteria)
		else:
			# TODO: Add an Expires header and respond to conditional GETs
			# headers.append(('Expires', ))
			pass
		query += ';'
		self._before_db()
		cursor = self.dbconn.cursor(cursors.DictCursor)
		try:
			cursor.execute('CALL ' + table_name + '_update();')
		except:
			# Can't refresh the report. Degrade gracefully by serving old data.
			pass
		try:
			cursor.execute(query)
		except:
			# Don't leak information about the database
			return webob.exc.HTTPBadRequest()
		return ( cursor.fetchall(), headers )

APIVersion.version_classes.append(APIv1App)

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
