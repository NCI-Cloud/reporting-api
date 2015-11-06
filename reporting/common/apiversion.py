"""
Abstract base class representing a particular version of an API spoken
by a WSGI application.
"""

import abc
from abc import abstractmethod
from reporting.common.authapp import KeystoneApplication


# This abstract base class is used by classes in other files,
# but pylint does not understand that because it processes files
# one at a time. The following comment silences a warning from pylint.
# pylint: disable=R0921

class APIVersion(KeystoneApplication):

    """
    Abstract base class representing a particular version of an API spoken
    by a WSGI application.
    """

    __metaclass__ = abc.ABCMeta

    version_classes = []

    @classmethod
    @abstractmethod
    def _version_identifier(cls):
        """
        Return a string uniquely identifying this API version.
        """
        pass

    @classmethod
    def _get_links(cls):
        """
        Return a dictionary of links to resources related to this API version.
        The keys should be the relationship of the other resource to this one,
        and the entries the URLs of those other resources.
        This is intended to be used to implement HATEOAS.
        """
        return dict()

    @classmethod
    def api_version_detail(cls, req, params):
        """
        Return details of this API version.
        """
        links = cls._get_links()
        links['self'] = "/" + cls._version_identifier()
        return dict(
            id=cls._version_identifier(),
            links=links
        )

    @classmethod
    def operation_APIVersionDetails(cls, req, params):
        """
        Return details of this API version.
        """
        return (cls.api_version_detail(req, params), None)
