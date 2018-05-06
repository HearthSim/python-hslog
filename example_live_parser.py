from time import sleep
import traceback

from hslog.live.parser import LiveLogParser

'''
    ----------------------------------------------------------------------
    LiveLogParser assumes that you've configured Power.log to be a symlink

    in "SOME_PATH/Hearthstone/Logs" folder:
        ln -s Power.log /tmp/hearthstone-redirected.log

    this will redirect all data coming into Power.log
    so we can access it from a RAM disk
    ----------------------------------------------------------------------
    For better performance make /tmp of type tmpfs (or another location)

    in /etc/fstab add line:
        tmpfs   /tmp         tmpfs   nodev,nosuid,size=1G          0  0

    this will create in-memory storage which is faster then SSD
    you need to restart the computer for this to take effect
    ----------------------------------------------------------------------
'''


def main():
    try:
        file = '/tmp/hearthstone-redirected.log'
        liveParser = LiveLogParser(file)
        liveParser.start()

        while True:
            sleep(1)

    except Exception as e:
        print(traceback.format_exc())
        liveParser.stop()


if __name__ == "__main__":
    main()
