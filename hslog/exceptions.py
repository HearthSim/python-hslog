"""Log parsing exceptions"""


class ParsingError(Exception):
	"""Generic exception that happens during log parsing."""
	pass


class RegexParsingError(ParsingError):
	pass


class CorruptLogError(ParsingError):
	"""Raised when a log is obviously corrupt, e.g. when containing NUL (0x00) bytes."""
	pass


class NoSuchEnum(ParsingError):
	"""Raised to indicate a log included an invalid enum value."""

	def __init__(self, enum, value):
		"""Ctor.

		:param enum: the enum type
		:param value: the value that couldn't be parsed
		"""

		super().__init__("Unhandled %s: %r" % (enum, value))

		self.enum = enum
		self.value = value


class ExporterError(Exception):
	"""Generic exception that happens during PacketTree export."""
	pass


class MissingPlayerData(RuntimeError):
	"""Raised when it is not possible to reverse a LazyPlayer instance."""
	pass
