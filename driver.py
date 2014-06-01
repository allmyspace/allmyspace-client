import sys
import os.path
import pyinotify
from space_providers.Dropbox import DropboxSyncClient
from DAL import DAL

options = {
    'watch-manager': None,
    'event-mask': pyinotify.IN_ATTRIB | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_DELETE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
}

DROPBOX_OAUTH_TOKEN = ''
DROPBOX_HOME_DIRECTORY = '/AllMySpace'

PROVIDER_DROPBOX = 'dropbox'
PROVIDER_BOX     = 'box'

dal = DAL()

def get_path_relative_to_watched_directory(original_path):
    global root_dir_path
    relative_path = ''
    if original_path.startswith(root_dir_path):
        relative_path = original_path[len(root_dir_path):]
    if relative_path.startswith('/'): return relative_path
    else : return '/' + relative_path

def get_dropbox_relative_path(relative_path):
    global DROPBOX_HOME_DIRECTORY
    return DROPBOX_HOME_DIRECTORY + relative_path

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
            return

        try:
            #TODO: Choose which one to call
            relative_path = get_path_relative_to_watched_directory(event.pathname)
            remote_path = dropbox_client.upload_file(get_dropbox_relative_path(relative_path), event.pathname)
            dal.add_file(relative_path, remote_path, PROVIDER_DROPBOX, int(os.path.getmtime(event.pathname)))

        except Exception as e:
            print e

    def process_IN_DELETE(self, event):
        self._file_object.write('%s: deleted at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) and (not os.path.islink(event.pathname)):
            return
        try:

            relative_path = get_path_relative_to_watched_directory(event.pathname)
            db_entry = dal.get_file_mappings(relative_path)
            print relative_path
            if db_entry['provider'] == PROVIDER_DROPBOX:
                dropbox_client.delete_file(db_entry['remote_path'])
            dal.delete_file(relative_path)

        except Exception as e:
            print e

    def process_IN_DELETE_SELF(self, event):
        test='test'

    def process_IN_IGNORED(self, event):
        test='test'

    def process_IN_MODIFY(self, event):
        self._file_object.write('%s: modified at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) and (not os.path.islink(event.pathname)):
                return
        try:
            relative_path = get_path_relative_to_watched_directory(event.pathname)
            db_entry = dal.get_file_mappings(relative_path)
            if db_entry['provider'] == PROVIDER_DROPBOX:
                dropbox_client.update_local_to_cloud(db_entry['remote_path'], event.pathname)
        except Exception as e:
            print e

    def process_IN_MOVE_SELF(self, event):
        test='test'

    def process_IN_MOVED_FROM(self, event):
        self._file_object.write('%s: moved at path %s with cookie = %s\n' % (event.name, event.pathname, event.cookie))
        if os.path.isdir(event.pathname) and (not os.path.islink(event.pathname)):
            return
        relative_path = get_path_relative_to_watched_directory(event.pathname)
        try:
            db_entry = dal.get_file_mappings(relative_path)
            if db_entry['provider'] == PROVIDER_DROPBOX:
                dropbox_client.delete_file(db_entry['remote_path'])
                dal.delete_file(relative_path)
        except Exception as e:
            print e

    def process_IN_MOVED_TO(self, event):
        self._file_object.write('%s: moved from %s to %s with cookie %s\n' % (event.name, event.src_pathname, event.pathname, event.cookie))
        self.process_IN_CREATE(event)

    def process_default(self, event):
        test='test'


def visit(options, dirname, names):
    if not os.path.islink(dirname):
        options['watch-manager'].add_watch(dirname, options['event-mask'])

if __name__ == '__main__':
    dropbox_client = DropboxSyncClient(DROPBOX_OAUTH_TOKEN)
    argsLen = len(sys.argv)
    if argsLen != 2:
        print("Usage: driver.py <allmyspace directory>")
        sys.exit(0)
    else:
        root_dir_path = str(sys.argv[1])
        if os.path.exists(root_dir_path) and (not os.path.islink(root_dir_path)) and os.path.isdir(root_dir_path):
            wm = pyinotify.WatchManager()
            options['watch-manager'] = wm
            os.path.walk(root_dir_path, visit, options)
            eventHandler = EventHandler()
            notifier = pyinotify.Notifier(wm, default_proc_fun=eventHandler)
            try:
                notifier.loop()
            except pyinotify.NotifierError, err:
                print >> sys.stderr, err
        else:
            print "The directory doesn't exist or the appropriate file permissions are not set"