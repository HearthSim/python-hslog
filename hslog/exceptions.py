"""
Log parsing exceptions
"""


class ParsingError(Exception):
	"""
	Generic exception that happens during log parsing.
	"""
	pass


class RegexParsingError(ParsingError):
	pass


class ExporterError(Exception):
	"""
	Generic exception that happens during PacketTree export.
	"""
	pass


class MissingPlayerData(RuntimeError):
	"""
	Raised when it is not possible to reverse a LazyPlayer instance.
	"""
	pass
