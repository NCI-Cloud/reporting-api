from reporting.common.apiversion import APIVersion
from reporting.common.application import Application


class VersionsApp(Application):

    def __init__(self):
        super(VersionsApp, self).__init__(None)

    def APIVersionList(self, req, args):
        return (
            [
                version._api_version_detail(req)
                for version in APIVersion.version_classes
            ],
            None
        )

    def APIVersionDetails(self, req, params):
        return (APIVersion._api_version_detail(req), None)


def app_factory(global_config, **settings):
    return VersionsApp()
