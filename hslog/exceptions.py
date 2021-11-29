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


class CorruptLogError(ParsingError):
	"""
	Raised when a log is obviously corrupt, for example when containing NUL (0x00) bytes.
	"""
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
