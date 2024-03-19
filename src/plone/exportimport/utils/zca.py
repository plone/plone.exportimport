from contextlib import contextmanager
from zope.interface import alsoProvides
from zope.interface import noLongerProvides
from zope.interface.interface import InterfaceClass
from ZPublisher.HTTPRequest import HTTPRequest


@contextmanager
def request_provides(request: HTTPRequest, interface: InterfaceClass):
    """Temporarily add the given interface to the request."""
    alsoProvides(request, interface)
    yield request
    noLongerProvides(request, interface)
