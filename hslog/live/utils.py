def align(text, size, char=" "):
	"""
		Format text to fit into a predefined amount of space

		Positive size aligns text to the left
		Negative size aligns text to the right
	"""
	text = str(text).strip()
	text_len = len(text)
	if text_len > abs(size):
		text = f"{text[:size-3]}..."
	offset = "".join(char * (abs(size) - text_len))
	if size < 0:
		return f"{offset}{text}"
	else:
		return f"{text}{offset}"


def color():
	def color_decorator(func):
		colors = {
			"LivePlayer": 93,
			"red": 31,
			"green": 32,
			"LiveGame": 33,
			"blue": 34,
			"purple": 35,
			"cyan": 36,
			"grey": 37,
		}

		def func_wrapper(msg_type, obj, *args):
			class_name = obj.__class__.__name__
			color_key = class_name if class_name in colors else "green"
			line = "\033[{}m{}\033[0m".format(colors[color_key], func(msg_type, obj, *args))
			print(line)

		return func_wrapper

	return color_decorator


@color()
def terminal_output(msg_type, obj, attr=None, value=None):
	return "{} | {} | {} | {}".format(
		align(msg_type, -20),
		align(repr(obj), 120),
		align(repr(attr), 40),
		align(value, 30),
	)


def debug_player_names(player_manager):
	print("{} | {} | {}".format(
		align(player_manager.actual_player_names, 40),
		align(player_manager.names_used, 40),
		align(player_manager.name_assignment_done, 10),
	))
