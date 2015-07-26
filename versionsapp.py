import json
from webob import Response
from apiversion import APIVersion
from application import Application
from apiv1app import APIv1App

class VersionsApp(Application):

	version_classes = [ APIv1App ]

	def APIVersionList(self, args):
		return Response(content_type = 'application/json', body = json.dumps([
			{
				"id": version._version_identifier(),
				"links": [
					{
						"href": "/" + version._version_identifier(),
						"rel": "self"
					}
				]
			} for version in self.version_classes
		]))

	def APIVersion(self, args):
		return Response(content_type = 'application/json', body = json.dumps({
			'todo': 'Report detail'
		}))

def factory(global_config, **settings):
	return VersionsApp()
