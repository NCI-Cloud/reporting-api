from common.apiversion import APIVersion
from common.application import Application

class VersionsApp(Application):

	def APIVersionList(self, req, args):
		return ( [ version._api_version_detail(req) for version in APIVersion.version_classes ], None )

	def APIVersionDetails(self, req, params):
		return ( APIVersion._api_version_detail(req), None )

def app_factory(global_config, **settings):
	return VersionsApp()
