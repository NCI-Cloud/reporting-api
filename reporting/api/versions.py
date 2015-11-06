from reporting.common.apiversion import APIVersion
from reporting.common.application import Application


class VersionsApp(Application):

    def __init__(self):
        super(VersionsApp, self).__init__(None)

    def operation_APIVersionList(self, req, params):
        return (
            [
                version.api_version_detail(req, params)
                for version in APIVersion.version_classes
            ],
            None
        )

    def operation_APIVersionDetails(self, req, params):
        """
        Return details of one API version.
        FIXME: This calls an abstract base class method.
        """
        return (APIVersion.api_version_detail(req, params), None)


def app_factory(global_config, **settings):
    return VersionsApp()
