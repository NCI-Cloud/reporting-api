from abc import abstractmethod
from reporting.common.authapp import KeystoneApplication


class APIVersion(KeystoneApplication):

    version_classes = []

    @classmethod
    @abstractmethod
    def _version_identifier(cls):
        pass

    @classmethod
    def _get_links(cls):
        return dict()

    @classmethod
    def api_version_detail(cls, req):
        links = cls._get_links()
        links['self'] = "/" + cls._version_identifier()
        return dict(
            id=cls._version_identifier(),
            links=links
        )

    @classmethod
    def operation_APIVersionDetails(cls, req, params):
        return (cls.api_version_detail(req), None)
