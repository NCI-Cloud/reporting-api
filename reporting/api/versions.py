"""
A WSGI application which lists available versions
of APIs understood by another WSGI application.
"""

from reporting.common.apiversion import APIVersion
from reporting.common.application import Application


class VersionsApp(Application):

    """
    A WSGI application which lists available versions
    of APIs understood by another WSGI application.
    """

    def __init__(self):
        super(VersionsApp, self).__init__(None)

    def operation_api_version_list(self, req, params):
        """
        Return a list of available API versions.
        """
        return (
            [
                version.api_version_detail(req, params)
                for version in APIVersion.version_classes
            ],
            None
        )

    def operation_api_version_details(self, req, params):
        """
        Return details of one API version.
        FIXME: This calls an abstract base class method.
        """
        return (APIVersion.api_version_detail(req, params), None)


def app_factory(global_config, **settings):
    """
    A factory function which returns WSGI version-list applications.
    """
    return VersionsApp()
