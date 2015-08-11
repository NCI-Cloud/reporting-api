import webob.exc
from common.apiversion import APIVersion
from common.application import Application

class VersionsApp(Application):

	def APIVersionList(self, req, args):
		return [ version._api_version_detail() for version in APIVersion.version_classes ]

	def APIVersionDetails(self, req, version_identifier):
		versions = [ version for version in APIVersion.version_classes if version._version_identifier() == version_identifier ]
		if not versions:
			return webob.exc.HTTPNotFound()
		if len(versions) > 1:
			raise RuntimeError("Multiple API versions with identifier '%s'" % version_identifier)
		return versions[0]._api_version_detail()

def factory(global_config, **settings):
	return VersionsApp()
