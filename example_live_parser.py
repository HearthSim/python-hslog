import traceback
from time import sleep

from hslog.live.parser import LiveLogParser


def main():
	"""
		----------------------------------------------------------------------
		LiveLogParser assumes that you"ve configured Power.log to be a symlink.

		In "SOME_PATH/Hearthstone/Logs" folder:
			ln -s Power.log /tmp/hearthstone-redirected.log

		This will redirect all data coming into Power.log
		so we can access it from a RAM disk.
		----------------------------------------------------------------------
		For better performance make /tmp of type tmpfs (or another location)

		In /etc/fstab add line:
			tmpfs	/tmp	tmpfs	nodev,nosuid,size=1G	0	0

		This will create in-memory storage which is faster then SSD.
		You need to restart the computer for this to take effect.
		----------------------------------------------------------------------
	"""
	try:
		file = "/tmp/hearthstone-redirected.log"
		liveParser = LiveLogParser(file)
		liveParser.start()

		while True:
			sleep(1)

	except Exception as e:
		print(traceback.format_exc())
		liveParser.stop()


if __name__ == "__main__":
	main()
