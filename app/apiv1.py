import ConfigParser
import webob.exc
from common.apiversion import APIVersion
from common.dbconn import DBConnection
from app.dbqueries import DBQueries

class APIv1App(APIVersion):

	def __init__(self, config_file):
		self.config = config_file
		self.dbname = self.config.get('database', 'dbname')
		self.dbconn = DBConnection(
			host = self.config.get('database', 'hostname'),
			user = self.config.get('database', 'username'),
			password = self.config.get('database', 'password'),
			database = self.dbname
		)

	@classmethod
	def _version_identifier(cls):
		return "v1"

	@classmethod
	def _get_links(cls):
		# TODO: Obtain this from the Swagger specification(s)
		return dict(
			reports = '/v1/reports'
		)

	@classmethod
	def _get_report_links(cls, report):
		# TODO: Obtain this from the Swagger specification(s)
		return dict(
			self = '/v1/reports/' + report
		)

	def _get_report_details(self, report_name):
		return dict(
				name = report_name,
				description = DBQueries._get_table_comment(self.dbconn, self.dbname, report_name),
				lastUpdated = DBQueries._get_table_lastupdate(self.dbconn, report_name),
				links = self._get_report_links(report_name)
			)

	def ReportsList(self, req, args):
		return ( [ self._get_report_details(report_name) for report_name in DBQueries._get_table_list(self.dbconn) ], None )

	def ReportResultSet(self, req, args):
		table_name = args['report']
		del args['report']
		if args:
			headers = None
		else:
			# TODO: Add an Expires header and respond to conditional GETs
			# headers.append(('Expires', ))
			headers = None
		try:
			result_set = DBQueries._filter_table(self.dbconn, table_name, args)
		except:
			# Don't leak information about the database
			return ( webob.exc.HTTPBadRequest(), None )
		return ( result_set, headers )

APIVersion.version_classes.append(APIv1App)

def factory(global_config, **settings):
	global_config.update(settings)
	config_file = global_config.get('config_file', 'apiv1app.ini')
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	return APIv1App(config)
