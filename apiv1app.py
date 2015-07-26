import json
from webob import Response
from apiversion import APIVersion

class APIv1App(APIVersion):

	@classmethod
	def _version_identifier(cls):
		return "v1";

	def ReportsList(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "List of reports" }))

	def ReportDetail(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "Report detail" }))

	def ReportResultSet(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "Report resultset" }))

def factory(global_config, **settings):
	return APIv1App()
