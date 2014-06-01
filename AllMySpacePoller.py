import time
import sys


class AllMySpacePoller():
    POLL_EVENT_FILENAME = ".poll"

    def __init__(self, root_dir_path, poll_delay):
        self.root_dir_path = root_dir_path
        self.poll_delay = poll_delay
        poll_event_file = open(root_dir_path + '/' + AllMySpacePoller.POLL_EVENT_FILENAME, 'w')
        poll_event_file.close()

    def poll(self):
        while True:
            print("waiting for %s secs ..." % str(self.poll_delay))
            time.sleep(self.poll_delay)
            try:
                poll_event_file = open(self.root_dir_path + '/' + AllMySpacePoller.POLL_EVENT_FILENAME, 'w')
                poll_event_file.write('polling')
                poll_event_file.close()
            except:
                pass

if __name__ == '__main__':
    argsLen = len(sys.argv)
    if argsLen != 3:
        print("Usage: AllMySpacePoller.py <allmyspace directory> <poll_delay>")
        sys.exit(0)
    else:
        root_dir_path = str(sys.argv[1])
        poll_delay = int(sys.argv[2])
        all_my_space_poller = AllMySpacePoller(root_dir_path, poll_delay)
        all_my_space_poller.poll()