from .parser import LogParser  # noqa


try:
	from importlib.metadata import version

	__version__ = version("hslog")
except ImportError:
	import pkg_resources

	__version__ = pkg_resources.require("hslog")[0].version
