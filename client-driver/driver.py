import sys
import os.path
import pyinotify

options = {
    'watch-manager': None,
    'event-mask': pyinotify.IN_ATTRIB | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_DELETE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
}

class EventHandler(pyinotify.ProcessEvent):

    def my_init(self, file_object=sys.stdout):
        self._file_object = file_object

    def process_IN_ATTRIB(self, event):
        self._file_object.write('%s: File metadata changed \n' % event.name)

    def process_IN_CLOSE_WRITE(self, event):
        test='test'

    def process_IN_CREATE(self, event):
        self._file_object.write('%s: created at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) and (not os.path.islink(event.pathname)):
            os.path.walk(event.pathname, visit, options)

    def process_IN_DELETE(self, event):
        self._file_object.write('%s: deleted at path %s\n' % (event.name, event.pathname))

    def process_IN_DELETE_SELF(self, event):
        test='test'

    def process_IN_IGNORED(self, event):
        test='test'

    def process_IN_MODIFY(self, event):
        self._file_object.write('%s: modified at path %s\n' % (event.name, event.pathname))

    def process_IN_MOVE_SELF(self, event):
        test='test'

    def process_IN_MOVED_FROM(self, event):
        self._file_object.write('%s: moved at path %s with cookie = %s\n' % (event.name, event.pathname, event.cookie))

    def process_IN_MOVED_TO(self, event):
        self._file_object.write('%s: moved from %s to %s with cookie %s\n' % (event.name, event.src_pathname, event.pathname, event.cookie))

    def process_default(self, event):
        test='test'


def visit(options, dirname, names):
    if not os.path.islink(dirname):
        options['watch-manager'].add_watch(dirname, options['event-mask'])

if __name__ == '__main__':
    argsLen = len(sys.argv)
    if argsLen != 2:
        print("Usage: driver.py <allmyspace directory>")
        sys.exit(0)
    else:
        rootDirPath = str(sys.argv[1])
        if os.path.exists(rootDirPath) and (not os.path.islink(rootDirPath)) and os.path.isdir(rootDirPath):
            wm = pyinotify.WatchManager()
            options['watch-manager'] = wm
            os.path.walk(rootDirPath, visit, options)
            eventHandler = EventHandler()
            notifier = pyinotify.Notifier(wm, default_proc_fun=eventHandler)
            try:
                notifier.loop()
            except pyinotify.NotifierError, err:
                print >> sys.stderr, err
        else:
            print "The directory doesn't exist or the appropriate file permissions are not set"