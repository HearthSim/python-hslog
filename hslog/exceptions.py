"""
Log parsing exceptions
"""


class ParsingError(Exception):
	pass


class RegexParsingError(ParsingError):
	pass


class MissingPlayerData(RuntimeError):
	"""
	Raised when it is not possible to reverse a LazyPlayer instance.
	"""
	pass
