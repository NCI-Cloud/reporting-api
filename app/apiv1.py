from datetime import datetime
import ConfigParser
from MySQLdb import cursors, escape_string
import webob.exc
from common.apiversion import APIVersion
from common.dbconn import DBConnection

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbname = self.config.get('database', 'dbname')
		self.dbconn = DBConnection(
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

	def _get_tables_comments(self, table_names):
		query = "SELECT table_comment FROM information_schema.tables WHERE table_schema=%s AND table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
		parameters = [ self.dbname ]
		parameters.extend(table_names)
		return [ row[0] for row in self.dbconn.execute(query, cursors.Cursor, parameters).fetchall() ]

	def _get_table_comment(self, table_name):
		return self._get_tables_comments([ table_name ])[0]

	def _get_table_lastupdates(self, table_names):
		query = "SELECT ts FROM metadata WHERE table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
		cursor = self.dbconn.execute(query, cursors.Cursor, table_names)
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
		query = 'SHOW TABLES;'
		cursor = self.dbconn.execute(query, cursors.Cursor)
		return ( [ self._get_report_details(row[0]) for row in cursor.fetchall() ], None )

	def ReportResultSet(self, req, args):
		table_name = args['report']
		del args['report']
		headers = None
		query = 'SELECT * FROM ' + escape_string(table_name)
		parameters = []
		if args:
			query += ' WHERE '
			criteria = []
			for (key, val) in args.items():
				criteria.append(escape_string(key) + "=%s")
				parameters.append(val[0])
			query += ' AND '.join(criteria)
		else:
			# TODO: Add an Expires header and respond to conditional GETs
			# headers.append(('Expires', ))
			pass
		query += ';'
		try:
			cursor = self.dbconn.execute('CALL ' + table_name + '_update();', cursors.DictCursor)
			cursor.fetchall()
		except:
			# Can't refresh the report. Degrade gracefully by serving old data.
			pass
		try:
			cursor = self.dbconn.execute(query, cursors.DictCursor, parameters)
		except:
			# Don't leak information about the database
			return ( webob.exc.HTTPBadRequest(), None )
		return ( cursor.fetchall(), headers )

APIVersion.version_classes.append(APIv1App)

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
