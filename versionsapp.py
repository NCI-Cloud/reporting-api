import json
from apiversion import APIVersion
from application import Application

class VersionsApp(Application):

	def respond(self):
		return [
			{
				"id": version.version_identifier(),
				"links": [
					{
						"href": "/" + version.version_identifier(),
						"rel": "self"
					}
				]
			} for version in APIVersion.__subclasses__()
		]

def factory(global_config, **settings):
	return VersionsApp
