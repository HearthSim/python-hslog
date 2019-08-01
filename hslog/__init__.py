import pkg_resources

from .parser import LogParser  # noqa


__version__ = pkg_resources.require("hslog")[0].version
